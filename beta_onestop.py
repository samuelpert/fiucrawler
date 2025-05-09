import asyncio
import os
from pathlib import Path
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter

async def discover_urls(base_url):
    """First phase: Discover URLs to crawl from the base URL and/or sitemap"""
    print(f"Discovering URLs from {base_url}...")
    
    # Specify the exact domain we want to limit crawling to
    target_domain = "onestop.fiu.edu"
    
    # Create discovery configuration
    discovery_config = CrawlerRunConfig(
        check_robots_txt=True,          
        exclude_external_links=True,    
    )
    
    # Create a crawler and discover URLs
    async with AsyncWebCrawler() as crawler:
        # Crawl the base URL to get links
        result = await crawler.arun(url=base_url, config=discovery_config)
        
        if result.success:
            # Extract internal links correctly with domain filtering
            discover_urls = []
            for link in result.links.get("internal", []):
                href = link.get("href", "")
                # Only include links from the target domain
                if href and target_domain in href and href != base_url:
                    discover_urls.append(href)
            
            # Remove duplicates while preserving order
            urls_to_crawl = list(dict.fromkeys(discover_urls))
            print(f"Discovered {len(urls_to_crawl)} unique URLs from {target_domain}")
            return urls_to_crawl
        else:
            print("Discovery was unsuccessful")
            return []
        
async def process_urls(base_url, selected_urls):
    """Process the selected URLs and save markdown content"""
    print("🔍 Processing selected URLs...")
    
    # Create output directory
    output_dir = "beta_onestop_content"
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize filter and markdown generator
    pruning_filter = PruningContentFilter(threshold=0.1, threshold_type="dynamic", min_word_threshold=5)
    md_generator = DefaultMarkdownGenerator(content_filter=pruning_filter)
    
    # Configure crawler
    config = CrawlerRunConfig(
        markdown_generator=md_generator,
        exclude_external_links=True,
        process_iframes=True,
        remove_overlay_elements=True,
        exclude_social_media_links=True,
        check_robots_txt=True,
    )
    
    # Initialize crawler and process URLs
    async with AsyncWebCrawler() as crawler:
        # Process URLs in smaller batches to manage memory usage
        batch_size = 5
        processed_results = []
        
        for i in range(0, len(selected_urls), batch_size):
            batch = selected_urls[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(len(selected_urls) + batch_size - 1)//batch_size} ({len(batch)} URLs)")
            
            # Process the batch
            batch_results = await crawler.arun_many(urls=batch, config=config)
            
            # Save output files
            for j, result in enumerate(batch_results):
                if result.success:
                    url_safe_name = result.url.split('/')[-1] or f"page_{i+j}"
                    
                    # Save raw markdown
                    raw_md_file = os.path.join(output_dir, f"result_raw_{url_safe_name}.md")
                    with open(raw_md_file, "w", encoding="utf-8") as f:
                        f.write(result.markdown.raw_markdown)
                    
                    # Save filtered markdown
                    filtered_md_file = os.path.join(output_dir, f"result_filtered_{url_safe_name}.md")
                    with open(filtered_md_file, "w", encoding="utf-8") as f:
                        f.write(result.markdown.fit_markdown)
                    
                    processed_results.append((result, raw_md_file, filtered_md_file))
                    print(f"Processed and saved {result.url}")
                else:
                    print(f"Failed to process {result.url}: {result.error}")
            
            # Small delay between batches
            if i + batch_size < len(selected_urls):
                await asyncio.sleep(2)
        
        return processed_results

async def main():
    # Base URL - defined at the beginning
    base_url = "https://onestop.fiu.edu"
    
    # Phase 1: Discover URLs
    urls_to_process = await discover_urls(base_url)
    
    if not urls_to_process:
        print("No URLs discovered. Using base URL only.")
        urls_to_process = [base_url]
    else:
        # Print discovered URLs for verification
        print("URLs to be processed:")
        for i, url in enumerate(urls_to_process[:10]):  # Show first 10
            print(f"  {i+1}. {url}")
        if len(urls_to_process) > 10:
            print(f"  ... and {len(urls_to_process) - 10} more URLs")
    
    # Phase 2: Process discovered URLs
    processed_results = await process_urls(base_url, urls_to_process)
    
    print(f"\nProcessed {len(processed_results)} pages total")
    print(f"All content saved to beta_onestop_content directory")

if __name__ == "__main__":
    asyncio.run(main())