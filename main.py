# main.py
import asyncio
import httpx
from pathlib import Path
from datetime import datetime
from fiu_sites import FIU_SITES
import xml.etree.ElementTree as ET


def create_markdown_filename(url, index=None):
    """Create a safe filename from URL"""
    # Remove protocol
    filename = url.replace("https://", "").replace("http://", "")
    # Replace special characters
    filename = filename.replace("/", "_").replace(".", "_").replace("?", "_")
    # Limit length
    filename = filename[:100]
    
    if index is not None:
        filename = f"{index:03d}_{filename}"
    
    return f"{filename}.md"

def save_markdown(content, metadata, site_name, url, index=None):
    """Save content as markdown file"""
    # Create directory structure
    base_dir = Path("fiu_content")
    site_dir = base_dir / site_name
    site_dir.mkdir(parents=True, exist_ok=True)
    
    # Create filename
    filename = create_markdown_filename(url, index)
    filepath = site_dir / filename
    
    # Prepare markdown content with metadata header
    markdown_content = f"""---
url: {url}
site: {site_name}
crawled_at: {metadata.get('crawled_at', datetime.now().isoformat())}
title: {metadata.get('title', 'No title')}
---

# {url}

{content}
"""
    
    # Save to file
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    
    print(f"💾 Saved: {filepath}")
    return filepath

async def parse_sitemap(sitemap_url):
    """Parse a sitemap XML and extract URLs"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(sitemap_url, follow_redirects=True)
            if response.status_code != 200:
                print(f"❌ Failed to fetch sitemap: {sitemap_url}")
                return []
            
            # Parse XML
            root = ET.fromstring(response.text)
            
            # Handle different namespaces
            namespaces = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            
            urls = []
            
            # Only exclude these specific file types
            exclude_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.mp4', '.js', '.webp', '.css', '.gif']
            
            # Try with namespace
            url_elements = root.findall('.//sm:url/sm:loc', namespaces)
            
            # If no URLs found, try without namespace
            if not url_elements:
                url_elements = root.findall('.//url/loc')
            
            # If still no URLs, check if it's a sitemap index
            if not url_elements:
                sitemap_elements = root.findall('.//sm:sitemap/sm:loc', namespaces)
                if not sitemap_elements:
                    sitemap_elements = root.findall('.//sitemap/loc')
                
                # Recursively parse sub-sitemaps
                for sitemap_elem in sitemap_elements:
                    sub_urls = await parse_sitemap(sitemap_elem.text)
                    urls.extend(sub_urls)
                return urls
            
            # Extract URLs
            excluded_count = 0
            for url_elem in url_elements:
                url = url_elem.text
                
                # Check if URL should be excluded
                should_exclude = False
                
                # Check file extensions (case insensitive)
                for ext in exclude_extensions:
                    if url.lower().endswith(ext):
                        should_exclude = True
                        excluded_count += 1
                        break
                
                if not should_exclude:
                    urls.append(url)
            
            print(f"  Found {len(url_elements)} URLs → {len(urls)} accepted ({excluded_count} excluded)")
            return urls
            
        except Exception as e:
            print(f"❌ Error parsing sitemap {sitemap_url}: {e}")
            return []

async def crawl_with_sitemap(site_config, sitemap_url):
    """Crawl using sitemap.xml"""
    print(f"\n🗺️ Crawling {site_config['name']} using sitemap")
    
    from crawl4ai import AsyncWebCrawler
    from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, CacheMode
    from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
    from crawl4ai.content_filter_strategy import PruningContentFilter
    
    # Get URLs from sitemap(s)
    all_urls = []
    sitemap_urls = site_config.get('sitemap_urls', [sitemap_url])
    
    for sitemap in sitemap_urls:
        print(f"📄 Parsing sitemap: {sitemap}")
        urls = await parse_sitemap(sitemap)
        all_urls.extend(urls)
        print(f"  Found {len(urls)} URLs")
    
    # Remove duplicates
    all_urls = list(set(all_urls))
    print(f"\n🔗 Total unique URLs to crawl: {len(all_urls)}")
    
    if not all_urls:
        print("❌ No URLs found in sitemap(s)")
        return
    
    # Configure browser and crawler
    browser_config = BrowserConfig()
    
    # Markdown generator with content filtering
    content_filter = PruningContentFilter(
        threshold=0.48,
        threshold_type="fixed"
    )
    markdown_generator = DefaultMarkdownGenerator(content_filter=content_filter)
    
    # Crawler configuration
    crawl_config = CrawlerRunConfig(
        markdown_generator=markdown_generator,
        cache_mode=CacheMode.BYPASS,
        check_robots_txt=True,
        exclude_external_links=True,
        process_iframes=True,
        remove_overlay_elements=True
    )
    
    # Crawl URLs in batches
    batch_size = 5
    site_folder = site_config['name'].lower().replace(" ", "_")
    successful_crawls = 0
    failed_crawls = 0
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        for i in range(0, len(all_urls), batch_size):
            batch = all_urls[i:i+batch_size]
            print(f"\n📦 Processing batch {i//batch_size + 1}/{(len(all_urls) + batch_size - 1)//batch_size}")
            
            # Use arun_many for batch processing
            results = await crawler.arun_many(urls=batch, config=crawl_config)
            
            # Process results
            for j, result in enumerate(results):
                url = batch[j]
                index = i + j + 1
                
                if result.success:
                    # Get markdown content
                    markdown_content = ""
                    if hasattr(result, 'markdown'):
                        if hasattr(result.markdown, 'fit_markdown'):
                            markdown_content = result.markdown.fit_markdown
                        else:
                            markdown_content = str(result.markdown)
                    
                    # Get metadata
                    metadata = {
                        'title': 'No title',
                        'crawled_at': datetime.now().isoformat()
                    }
                    if hasattr(result, 'metadata'):
                        metadata.update(result.metadata)
                    
                    # Save to markdown
                    save_markdown(
                        content=markdown_content,
                        metadata=metadata,
                        site_name=site_folder,
                        url=url,
                        index=index
                    )
                    successful_crawls += 1
                else:
                    # Save error file
                    error_content = f"Couldn't crawl due to error: {result.error if hasattr(result, 'error') else 'Unknown error'}"
                    error_metadata = {
                        'title': 'Error',
                        'crawled_at': datetime.now().isoformat(),
                        'error': str(result.error) if hasattr(result, 'error') else 'Unknown error'
                    }
                    
                    save_markdown(
                        content=error_content,
                        metadata=error_metadata,
                        site_name=site_folder,
                        url=url,
                        index=index
                    )
                    failed_crawls += 1
                    print(f"  ❌ Failed: {url}")
            
            # Small delay between batches
            if i + batch_size < len(all_urls):
                await asyncio.sleep(2)
    
    print(f"\n📊 Crawl Summary:")
    print(f"  ✅ Successful: {successful_crawls}")
    print(f"  ❌ Failed: {failed_crawls}")
    print(f"  📁 Total files: {successful_crawls + failed_crawls}")


async def check_for_sitemap(site_config):
    """Check if a site has a sitemap"""
    sitemap_urls = site_config.get('sitemap_urls', [])
    
    if not sitemap_urls:
        # Try common patterns if no sitemap URLs provided
        sitemap_urls = site_config.get('possible_sitemaps', [])
    
    if sitemap_urls:
        print(f"✅ Site has {len(sitemap_urls)} configured sitemap(s)")
        return sitemap_urls[0]  # Return first sitemap for compatibility
    
    print(f"❌ No sitemap configured for {site_config['name']}")
    return None

async def crawl_with_deep_crawl(site_config):
    """Crawl using deep crawl strategy"""
    print(f"\n🕷️ Crawling {site_config['name']} using deep crawl")
    
    from crawl4ai import AsyncWebCrawler, BFSDeepCrawlStrategy
    from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, CacheMode
    from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
    from crawl4ai.content_filter_strategy import PruningContentFilter
    
    # Configure browser
    browser_config = BrowserConfig()
    
    # Deep crawl strategy
    deep_crawl_strategy = BFSDeepCrawlStrategy(
        max_depth=2,
        max_pages=10  # Start small for testing
    )
    
    # Markdown generator with content filtering
    content_filter = PruningContentFilter(
        threshold=0.48,
        threshold_type="fixed"
    )
    markdown_generator = DefaultMarkdownGenerator(content_filter=content_filter)
    
    # Crawler configuration
    crawl_config = CrawlerRunConfig(
        deep_crawl_strategy=deep_crawl_strategy,
        markdown_generator=markdown_generator,
        cache_mode=CacheMode.BYPASS,
        exclude_external_links=True,
        check_robots_txt=True
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun(
            url=site_config['base_url'],
            config=crawl_config
        )
        
        # Process results
        if not isinstance(results, list):
            results = [results]
        
        print(f"Found {len(results)} pages")
        
        # Save each result
        for i, result in enumerate(results):
            if result.success:
                # Get markdown content
                markdown_content = ""
                if hasattr(result, 'markdown'):
                    if hasattr(result.markdown, 'fit_markdown'):
                        markdown_content = result.markdown.fit_markdown
                    else:
                        markdown_content = str(result.markdown)
                
                # Get metadata
                metadata = {
                    'title': 'No title',
                    'crawled_at': datetime.now().isoformat()
                }
                if hasattr(result, 'metadata'):
                    metadata.update(result.metadata)
                
                # Save to markdown
                save_markdown(
                    content=markdown_content,
                    metadata=metadata,
                    site_name=site_config['name'].lower().replace(" ", "_"),
                    url=result.url,
                    index=i+1
                )

async def crawl_site(site_key):
    """Main function to crawl a single site"""
    if site_key not in FIU_SITES:
        print(f"Unknown site: {site_key}")
        return
    
    site_config = FIU_SITES[site_key]
    print(f"\n{'='*50}")
    print(f"Starting crawl for: {site_config['name']}")
    print(f"Base URL: {site_config['base_url']}")
    print(f"{'='*50}")
    
    # Check for sitemap
    sitemap_url = await check_for_sitemap(site_config)
    
    if sitemap_url:
        # Use sitemap approach
        await crawl_with_sitemap(site_config, sitemap_url)
    else:
        # Use deep crawl approach
        await crawl_with_deep_crawl(site_config)
    
    # Print summary
    site_dir = Path("fiu_content") / site_config['name'].lower().replace(" ", "_")
    if site_dir.exists():
        md_files = list(site_dir.glob("*.md"))
        print(f"\n✅ Crawl complete. Saved {len(md_files)} files to {site_dir}")

async def main():
    """Main entry point"""
    # Create base directory
    Path("fiu_content").mkdir(exist_ok=True)
    
    # For now, let's just crawl OneStop
    await crawl_site("admissions")

if __name__ == "__main__":
    asyncio.run(main())