import argparse
import asyncio
from urllib.parse import urlparse
from crawl4ai import AsyncWebCrawler, BFSDeepCrawlStrategy, BrowserConfig, CacheMode, CrawlerRunConfig, DefaultMarkdownGenerator, DomainFilter, FilterChain, LXMLWebScrapingStrategy, PruningContentFilter
import httpx
from pathlib import Path
from datetime import datetime
from fiu_sites import FIU_SITES
import xml.etree.ElementTree as ET


async def extract_pdfs_from_site(site_config):
    """Extract all PDF links from a website using deep crawl specifically for PDFs"""
    base_url = site_config['base_url']
    domain = urlparse(base_url).netloc
    print(f"\n📄 Extracting PDFs from {site_config['name']} ({base_url})")
    
    # Define domain filter for the specific site
    filter_chain = FilterChain([
        DomainFilter(allowed_domains=[domain]),
    ])

    browser_config = BrowserConfig(
        headless=True,
        browser_type="chrome",
        verbose=False
    )

    # Configure deeper crawl specifically for PDFs
    config = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=3,  # Go deeper for PDFs
            max_pages=1000,  # More pages to find all PDFs
            filter_chain=filter_chain
        ),
        verbose=True,
    )

    # Process results after crawling
    pdf_urls = set()  # Use a set to avoid duplicates
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Custom link filter to help find PDFs
        def enhanced_pdf_link_filter(url):
            # Keep URLs from same domain and specifically look for PDF-related patterns
            url_lower = url.lower()
            url_domain = urlparse(url).netloc
            is_same_domain = (url_domain == domain or not url_domain)
            
            # Always accept PDFs
            if url_lower.endswith('.pdf'):
                return True
                
            # Accept URLs that might lead to PDFs
            pdf_patterns = ['/pdf/', '/pdfs/', '/documents/', '/downloads/', '/files/']
            might_lead_to_pdf = any(pattern in url_lower for pattern in pdf_patterns)
            
            return is_same_domain and (might_lead_to_pdf or '/download' in url_lower)
            
        crawler.link_filter = enhanced_pdf_link_filter
        
        try:
            results = await crawler.arun(base_url, config=config)
            
            # Handle both single result and list
            if not isinstance(results, list):
                results = [results]
            
            # Post-process to filter PDFs
            for result in results:
                if hasattr(result, 'url') and result.url.lower().endswith('.pdf'):
                    pdf_urls.add(result.url)
                    print(f"  🔍 Found PDF: {result.url}")
        except Exception as e:
            print(f"  ❌ Error during PDF extraction: {str(e)}")

    print(f"  ✅ Found {len(pdf_urls)} unique PDF files")
    return pdf_urls



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
            
            # Remove this line - we'll use the shared function instead
            # exclude_extensions = ['.jpg', '.jpeg', '.png', '.mp4', '.js', '.webp', '.css', '.gif']
            
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
            
            # Extract URLs - REPLACE THIS ENTIRE SECTION
            excluded_count = 0
            for url_elem in url_elements:
                url = url_elem.text
                
                # Use the shared function instead of inline logic
                if not should_exclude_url(url):
                    urls.append(url)
                else:
                    excluded_count += 1
            
            print(f"  Found {len(url_elements)} URLs → {len(urls)} accepted ({excluded_count} excluded)")
            return urls
            
        except Exception as e:
            print(f"❌ Error parsing sitemap {sitemap_url}: {e}")
            return []

async def crawl_with_sitemap(site_config, sitemap_url, threshold=0.30):
    """Crawl using sitemap.xml with PDF extraction and 404 error detection"""
    print(f"\n🗺️ Crawling {site_config['name']} using sitemap")
    print(f"  Parameters: threshold={threshold}")
    
    # First extract all PDFs from the site using deep crawl
    pdf_urls = await extract_pdfs_from_site(site_config)
    print(f"📊 PDF Extraction: Found {len(pdf_urls)} unique PDF files")
    
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
    
    # Create PDF index file
    site_folder = site_config['name'].lower().replace(" ", "_")
    if pdf_urls:
        pdf_dir = Path("fiu_content") / site_folder
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_index_path = pdf_dir / "pdf_index.md"
        
        with open(pdf_index_path, "w", encoding="utf-8") as f:
            f.write(f"""---
url: {site_config['base_url']}/pdf_index
site: {site_config['name']}
crawled_at: {datetime.now().isoformat()}
title: PDF Index - {site_config['name']}
---

# PDF Resources for {site_config['name']}

This document contains all PDF resources found on {site_config['base_url']}.

## PDF Files ({len(pdf_urls)})

""")
            # Sort PDFs by filename for better organization
            sorted_pdfs = sorted(pdf_urls, key=lambda x: x.split("/")[-1].lower())
            for pdf_url in sorted_pdfs:
                # Extract filename from URL for better display
                filename = pdf_url.split("/")[-1]
                # Create markdown link
                f.write(f"- [{filename}]({pdf_url})\n")
                
        print(f"📄 Created PDF index with {len(pdf_urls)} files")
    
    # Now continue with regular content crawling using sitemap URLs
    # Configure browser for sitemap crawling
    browser_cfg = BrowserConfig(
        headless=True,
        browser_type="chrome",
        verbose=False
    )
    # Crawl URLs in batches
    batch_size = 100
    successful_crawls = 0
    failed_crawls = 0
    error_pages = 0
    
    # Define patterns that indicate error pages
    error_patterns = [
        "Page Not Found",
        "ERROR 404",
        "error 404",
        "Error 404",
    ]


    markdown_generator = DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(threshold=threshold, threshold_type="dynamic")
    )

    my_run_config = CrawlerRunConfig(
        markdown_generator=markdown_generator,
        check_robots_txt=True,
        cache_mode=CacheMode.BYPASS,
        verbose=True,
        excluded_tags=["footer", "nav", "header"], # Remove entire tag blocks
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        for i in range(0, len(all_urls), batch_size):
            batch = all_urls[i:i+batch_size]
            print(f"\n📦 Processing batch {i//batch_size + 1}/{(len(all_urls) + batch_size - 1)//batch_size}")
            
            # Use arun_many for batch processing
            results = await crawler.arun_many(urls=batch, config=my_run_config)
            
            # Process results
            for j, result in enumerate(results):
                raw_url = batch[j]
                url = getattr(result, 'url', raw_url)  # Use actual crawled URL if available
                index = i + j + 1
                
                # Skip PDFs in regular content crawling since we already processed them
                if url.lower().endswith('.pdf'):
                    continue
                
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
                        if pattern.lower() in content_lower or pattern.lower() in title:
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
                    
                    # REMOVED: The insufficient content check that was here
                    
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
                    print(f"  ✅ Saved: {url}")
                else:
                    # [rest of error handling remains the same]
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
    print(f"  ✅ Successful pages: {successful_crawls}")
    print(f"  ❌ Failed pages: {failed_crawls}")
    print(f"  ⚠️ Error pages (404): {error_pages}")
    print(f"  📄 PDF files discovered: {len(pdf_urls)}")
    print(f"  📁 Total files: {successful_crawls + failed_crawls + error_pages + (1 if pdf_urls else 0)}")
    
    return successful_crawls, failed_crawls, error_pages, len(pdf_urls)


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

def should_exclude_url(url, exclude_extensions=None, exclude_patterns=None):
    """Check if URL should be excluded based on extensions and patterns"""
    if exclude_extensions is None:
        exclude_extensions = ['.jpg', '.jpeg', '.png', '.mp4', '.js', '.webp', '.css', '.gif']
    if exclude_patterns is None:
        exclude_patterns = ['/download/', '/print/', '#', 'javascript:', 'mailto:']
    
    url_lower = url.lower()
    
    # Check extensions
    for ext in exclude_extensions:
        if url_lower.endswith(ext):
            return True
    
    # Check patterns
    for pattern in exclude_patterns:
        if pattern in url_lower:
            return True
    
    return False


async def crawl_with_deep_crawl(site_cfg: dict, max_depth: int = 2, max_pages: int = 400, threshold=0.30):
    base = site_cfg["base_url"]
    host = urlparse(base).netloc.lower()
    site_folder = site_cfg['name'].lower().replace(" ", "_")
    print(f"\n🕷️ Deep crawling {site_cfg['name']} @ {base}")
    print(f"  Parameters: max_depth={max_depth}, max_pages={max_pages}, threshold={threshold}")



    filter_chain = FilterChain([
        DomainFilter(allowed_domains=[host]),
    ])
    
    browser_cfg = BrowserConfig()
    bfs = BFSDeepCrawlStrategy(max_depth=max_depth, max_pages=max_pages, filter_chain=filter_chain)
    md_gen = DefaultMarkdownGenerator(content_filter=PruningContentFilter(threshold, "fixed"))
    cfg = CrawlerRunConfig(
        deep_crawl_strategy=bfs,
        markdown_generator=md_gen,
        cache_mode=CacheMode.BYPASS,
        exclude_external_links=True,
        check_robots_txt=True,
        process_iframes=True,
        remove_overlay_elements=True
    )
    
    successful_crawls = 0
    failed_crawls = 0
    error_pages = 0
    
    # Define error page patterns same as sitemap
    error_patterns = [
        "Page Not Found",
        "ERROR 404", 
        "error 404",
        "Error 404",
    ]
    
    async with AsyncWebCrawler(config=browser_cfg) as cr:
        # Stricter link filter that checks the exact host
        cr.link_filter = lambda u: urlparse(u).netloc.lower() == host and not any(ext in u.lower() for ext in ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.css', '.js'])
        results = await cr.arun(base, config=cfg)
        
        # Handle single result or list
        if not isinstance(results, list):
            results = [results]
    
    print(f"→ Found {len(results)} pages under {host}")
    
    for idx, res in enumerate(results, start=1):
        u = res.url if hasattr(res, 'url') else base
        
        if res.success:
            content = ""
            if hasattr(res, "markdown"):
                if isinstance(res.markdown, str):
                    content = res.markdown
                elif hasattr(res.markdown, "fit_markdown"):
                    content = str(res.markdown.fit_markdown)
                else:
                    content = str(res.markdown)
            
            # Check for error page patterns
            content_lower = content.lower()
            is_error_page = False
            
            # Get metadata and title
            metadata = getattr(res, "metadata", {})
            title = metadata.get('title', '')
            title_lower = title.lower()
            
            # Check both content and title for error patterns
            for pattern in error_patterns:
                if pattern in content_lower or pattern in title_lower:
                    is_error_page = True
                    break
            
            # Also check HTTP status if available
            if hasattr(res, 'status_code') and res.status_code == 404:
                is_error_page = True
            
            if is_error_page:
                error_pages += 1
                print(f"  ⚠️ Error page detected: {u}")
                
                # Save error page info
                error_metadata = {
                    'title': 'Error Page - 404',
                    'crawled_at': datetime.now().isoformat(),
                    'error_type': '404_page'
                }
                
                save_markdown(
                    content=f"Error page detected. URL may be broken.\n\n{content[:500]}...",
                    metadata=error_metadata,
                    site_name=site_folder + "_errors",
                    url=u,
                    index=idx
                )
                continue
            
            # Skip if content is too short
            if len(content.strip()) < 100:
                print(f"  ⚠️ Skipping {u} - insufficient content")
                failed_crawls += 1
                continue
            
            # Enhanced metadata
            enhanced_metadata = {
                'title': title if title else 'No title',
                'crawled_at': datetime.now().isoformat(),
                'depth': metadata.get('depth', 0)
            }
            enhanced_metadata.update(metadata)
            
            save_markdown(content, enhanced_metadata, site_folder, u, index=idx)
            successful_crawls += 1
            print(f"✅ {u}")
        else:
            failed_crawls += 1
            error_msg = getattr(res,'error','Unknown error')
            print(f"❌ {u} failed: {error_msg}")
            
            # Save error file
            error_metadata = {
                'title': 'Crawl Error',
                'crawled_at': datetime.now().isoformat(),
                'error': str(error_msg)
            }
            
            save_markdown(
                content=f"Couldn't crawl due to error: {error_msg}",
                metadata=error_metadata,
                site_name=site_folder + "_errors",
                url=u,
                index=idx
            )
    
    # Print summary
    print(f"\n📊 Deep Crawl Summary:")
    print(f"  ✅ Successful: {successful_crawls}")
    print(f"  ❌ Failed: {failed_crawls}")
    print(f"  ⚠️ Error pages (404): {error_pages}")
    print(f"  📁 Total files: {successful_crawls + failed_crawls + error_pages}")
    print(f"  💾 Content saved to: {Path('fiu_content') / site_folder}")
    
    # RETURN THE STATISTICS!
    return successful_crawls, failed_crawls, error_pages

# Update the crawl_site function to pass parameters
async def crawl_site(site_key, max_depth: int = 2, max_pages: int = 400, threshold=0.30):
    """Main function to crawl a single site with parameters"""
    if site_key not in FIU_SITES:
        print(f"Unknown site: {site_key}")
        return
    
    site_config = FIU_SITES[site_key]
    print(f"\n{'='*50}")
    print(f"Starting crawl for: {site_config['name']}")
    print(f"Base URL: {site_config['base_url']}")


    # Different parameter display based on crawl type
    if 'sitemap_urls' in site_config:
        print(f"Crawl type: Sitemap-based")
        print(f"Parameters: threshold={threshold}")
    else:
        print(f"Crawl type: Deep crawl")
        print(f"Parameters: max_depth={max_depth}, max_pages={max_pages}, threshold={threshold}")
    print(f"{'='*50}")
    
    # Check for sitemap
    sitemap_url = await check_for_sitemap(site_config)
    
    if sitemap_url:
        # Use sitemap approach
        await crawl_with_sitemap(site_config, sitemap_url, threshold=threshold)
    else:
        # Use deep crawl approach
        await crawl_with_deep_crawl(site_config, max_depth=max_depth, max_pages=max_pages, threshold=threshold)  # Pass parameters
    
    # Print summary
    site_dir = Path("fiu_content") / site_config['name'].lower().replace(" ", "_")
    if site_dir.exists():
        md_files = list(site_dir.glob("*.md"))
        print(f"\n✅ Crawl complete. Saved {len(md_files)} files to {site_dir}")

# Update main function to test with parameters
async def main():
    """Main entry point with command line argument parsing"""
    # Create an argument parser
    parser = argparse.ArgumentParser(description='FIU Website Crawler')
    
    # Add arguments
    parser.add_argument('site_key', help='Site key from fiu_sites.py (e.g., "onestop", "dem", "admissions")')
    parser.add_argument('--max-depth', type=int, default=2, help='Maximum crawl depth for deep crawling (default: 2)')
    parser.add_argument('--max-pages', type=int, default=400, help='Maximum number of pages to crawl (default: 400)')
    parser.add_argument('--threshold', type=float, default=0.48, help='Content filtering threshold (default: 0.48)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Validate site key
    if args.site_key not in FIU_SITES:
        print(f"Error: Unknown site key '{args.site_key}'. Available site keys are: {', '.join(FIU_SITES.keys())}")
        return
    
    # Create base directory
    Path("fiu_content").mkdir(exist_ok=True)
    
    # Run the crawler with provided parameters
    print(f"Starting crawl for {args.site_key} with parameters:")
    print(f"  max_depth: {args.max_depth}")
    print(f"  max_pages: {args.max_pages}")
    print(f"  threshold: {args.threshold}")
    
    await crawl_site(
        args.site_key, 
        max_depth=args.max_depth, 
        max_pages=args.max_pages, 
        threshold=args.threshold
    )



if __name__ == "__main__":
    asyncio.run(main())