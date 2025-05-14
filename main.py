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
            exclude_extensions = ['.jpg', '.jpeg', '.png', '.mp4', '.js', '.webp', '.css', '.gif']
            
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
    """Crawl using sitemap.xml with 404 error detection"""
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
    error_pages = 0  # Track 404/error pages
    
    # Define patterns that indicate error pages
    error_patterns = [
        "Page Not Found",
        "ERROR 404",
        "error 404",
        "Error 404",
    ]
    
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
                    
                    # Check for error page patterns
                    content_lower = markdown_content.lower()
                    is_error_page = False
                    
                    # Check title for error patterns
                    title = ""
                    if hasattr(result, 'metadata') and result.metadata.get('title'):
                        title = result.metadata.get('title', '').lower()
                    
                    # Check both content and title for error patterns
                    for pattern in error_patterns:
                        if pattern in content_lower or pattern in title:
                            is_error_page = True
                            break
                    
                    # Also check HTTP status if available
                    if hasattr(result, 'status_code') and result.status_code == 404:
                        is_error_page = True
                    
                    if is_error_page:
                        error_pages += 1
                        print(f"  ⚠️ Error page detected: {url}")
                        
                        # Optionally save error page info for debugging
                        error_metadata = {
                            'title': 'Error Page - 404',
                            'crawled_at': datetime.now().isoformat(),
                            'error_type': '404_page'
                        }
                        
                        save_markdown(
                            content=f"Error page detected. URL may be outdated in sitemap.\n\n{markdown_content[:500]}...",
                            metadata=error_metadata,
                            site_name=site_folder + "_errors",
                            url=url,
                            index=index
                        )
                        continue
                    
                    # Skip if content is too short (might be error page)
                    if len(markdown_content.strip()) < 100:
                        print(f"  ⚠️ Skipping {url} - insufficient content")
                        failed_crawls += 1
                        continue
                    
                    # Get metadata
                    metadata = {
                        'title': title if title else 'No title',
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
                        'title': 'Crawl Error',
                        'crawled_at': datetime.now().isoformat(),
                        'error': str(result.error) if hasattr(result, 'error') else 'Unknown error'
                    }
                    
                    save_markdown(
                        content=error_content,
                        metadata=error_metadata,
                        site_name=site_folder + "_errors",
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
    print(f"  ⚠️ Error pages (404): {error_pages}")
    print(f"  📁 Total files: {successful_crawls + failed_crawls + error_pages}")


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

async def crawl_with_deep_crawl(site_config, max_depth=3, max_pages=100, threshold=0.48):
    """Crawl using deep crawl strategy with configurable parameters and error page detection"""
    print(f"\n🕷️ Crawling {site_config['name']} using deep crawl")
    print(f"  Max depth: {max_depth}")
    print(f"  Max pages: {max_pages}")
    print(f"  Content threshold: {threshold}")
    
    from crawl4ai import AsyncWebCrawler, BFSDeepCrawlStrategy
    from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, CacheMode
    from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
    from crawl4ai.content_filter_strategy import PruningContentFilter
    
    # Configure browser with better settings
    browser_config = BrowserConfig(
        headless=True,
        verbose=False,
        page_timeout=30000,  # 30 seconds
        wait_until="networkidle"
    )
    
    # Enhanced deep crawl strategy
    deep_crawl_strategy = BFSDeepCrawlStrategy(
        max_depth=max_depth,
        max_pages=max_pages,
        same_domain_only=True,
        exclude_patterns=[
            r".*\.(jpg|jpeg|png|gif|mp4|pdf|zip|exe|dmg)$",
            r".*/download/.*",
            r".*/print/.*",
            r"#.*",
            r"javascript:.*",
            r"mailto:.*"
        ],
        wait_time=1.0,  # Wait between requests
        respect_robots_txt=True
    )
    
    # Markdown generator with configurable content filtering
    content_filter = PruningContentFilter(
        threshold=threshold,
        threshold_type="fixed",
        exclude_selectors=[
            "nav", "footer", "header",
            ".navigation", ".menu", 
            ".ads", ".banner",
            "#comments"
        ],
        min_word_threshold=100
    )
    markdown_generator = DefaultMarkdownGenerator(content_filter=content_filter)
    
    # Crawler configuration
    crawl_config = CrawlerRunConfig(
        deep_crawl_strategy=deep_crawl_strategy,
        markdown_generator=markdown_generator,
        cache_mode=CacheMode.BYPASS,
        exclude_external_links=True,
        check_robots_txt=True,
        remove_overlay_elements=True,
        process_iframes=False,
        delay_after_load=1.5,
        verbose=False,
        screenshot=False
    )
    
    successful_crawls = 0
    failed_crawls = 0
    error_pages = 0  # Track 404/error pages
    site_folder = site_config['name'].lower().replace(" ", "_")
    crawled_urls = set()
    
    # Define patterns that indicate error pages
    error_patterns = [
        "Page Not Found",
        "ERROR 404",
        "error 404",
        "Error 404",
    ]
    
    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            results = await crawler.arun(
                url=site_config['base_url'],
                config=crawl_config
            )
            
            # Handle single result or list
            if not isinstance(results, list):
                results = [results]
            
            print(f"\n📊 Found {len(results)} pages during deep crawl")
            
            # Process each result
            for i, result in enumerate(results, 1):
                try:
                    # Skip duplicates
                    if hasattr(result, 'url') and result.url in crawled_urls:
                        continue
                    
                    if result.success:
                        url = result.url if hasattr(result, 'url') else site_config['base_url']
                        crawled_urls.add(url)
                        
                        # Extract markdown content
                        markdown_content = ""
                        if hasattr(result, 'markdown'):
                            if hasattr(result.markdown, 'fit_markdown'):
                                markdown_content = result.markdown.fit_markdown
                            else:
                                markdown_content = str(result.markdown)
                        
                        # Check for error page patterns
                        content_lower = markdown_content.lower()
                        is_error_page = False
                        
                        # Check title for error patterns
                        title = ""
                        if hasattr(result, 'metadata') and result.metadata.get('title'):
                            title = result.metadata.get('title', '')
                            title_lower = title.lower()
                        else:
                            title_lower = ""
                        
                        # Check both content and title for error patterns
                        for pattern in error_patterns:
                            if pattern in content_lower or pattern in title_lower:
                                is_error_page = True
                                break
                        
                        # Also check HTTP status if available
                        if hasattr(result, 'status_code') and result.status_code == 404:
                            is_error_page = True
                        
                        # Check for very short content (often error pages)
                        if len(markdown_content.strip()) < 100:
                            # If very short, check more carefully for error indicators
                            if "404" in content_lower or "not found" in content_lower:
                                is_error_page = True
                        
                        if is_error_page:
                            error_pages += 1
                            print(f"  ⚠️ Error page detected: {url[:50]}...")
                            
                            # Optionally save error page info for debugging
                            error_metadata = {
                                'title': 'Error Page - 404',
                                'crawled_at': datetime.now().isoformat(),
                                'error_type': '404_page',
                                'original_title': title
                            }
                            
                            save_markdown(
                                content=f"Error page detected. URL may be broken.\n\n{markdown_content[:500]}...",
                                metadata=error_metadata,
                                site_name=site_folder + "_errors",
                                url=url,
                                index=i
                            )
                            continue
                        
                        # Skip if content too short (but not already caught as error)
                        if len(markdown_content.strip()) < 200:
                            print(f"  ⚠️ Skipping {url[:50]}... - insufficient content")
                            continue
                        
                        # Enhanced metadata extraction
                        metadata = {
                            'crawled_at': datetime.now().isoformat(),
                            'depth': result.metadata.get('depth', 0) if hasattr(result, 'metadata') else 0,
                            'title': title if title else 'No title'
                        }
                        
                        if hasattr(result, 'metadata'):
                            metadata.update({
                                'description': result.metadata.get('description', ''),
                                'keywords': result.metadata.get('keywords', ''),
                                'author': result.metadata.get('author', ''),
                                'language': result.metadata.get('language', 'en')
                            })
                        
                        # Save to markdown
                        save_markdown(
                            content=markdown_content,
                            metadata=metadata,
                            site_name=site_folder,
                            url=url,
                            index=i
                        )
                        successful_crawls += 1
                        
                        # Progress update
                        if successful_crawls % 10 == 0:
                            print(f"  ✅ Progress: {successful_crawls} pages saved")
                    
                    else:
                        failed_crawls += 1
                        error_msg = result.error if hasattr(result, 'error') else 'Unknown error'
                        print(f"  ❌ Failed page {i}: {error_msg[:50]}...")
                        
                        # Save crawl error info
                        if hasattr(result, 'url'):
                            error_metadata = {
                                'crawled_at': datetime.now().isoformat(),
                                'error': str(error_msg),
                                'title': 'Crawl Error'
                            }
                            save_markdown(
                                content=f"Failed to crawl this page.\n\nError: {error_msg}",
                                metadata=error_metadata,
                                site_name=site_folder + "_errors",
                                url=result.url,
                                index=i
                            )
                
                except Exception as e:
                    failed_crawls += 1
                    print(f"  ❌ Error processing result {i}: {str(e)}")
                    continue
                    
    except Exception as e:
        print(f"\n❌ Crawler error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Print summary
    print(f"\n📊 Deep Crawl Summary:")
    print(f"  ✅ Successful: {successful_crawls}")
    print(f"  ❌ Failed: {failed_crawls}")
    print(f"  ⚠️ Error pages (404): {error_pages}")
    print(f"  📁 Total unique URLs: {len(crawled_urls)}")
    print(f"  💾 Content saved to: {Path('fiu_content') / site_folder}")
    
    return successful_crawls, failed_crawls, error_pages


# Update the crawl_site function to pass parameters
async def crawl_site(site_key, max_depth=3, max_pages=100, threshold=0.48):
    """Main function to crawl a single site with parameters"""
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
        # Use deep crawl approach with parameters
        await crawl_with_deep_crawl(site_config, max_depth, max_pages, threshold)
    
    # Print summary
    site_dir = Path("fiu_content") / site_config['name'].lower().replace(" ", "_")
    if site_dir.exists():
        md_files = list(site_dir.glob("*.md"))
        print(f"\n✅ Crawl complete. Saved {len(md_files)} files to {site_dir}")


# Update main function to test with parameters
async def main():
    """Main entry point"""
    # Create base directory
    Path("fiu_content").mkdir(exist_ok=True)
    
    # Test with custom parameters
    await crawl_site("commencement")
    


if __name__ == "__main__":
    asyncio.run(main())