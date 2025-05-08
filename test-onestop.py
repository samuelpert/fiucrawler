import asyncio
import crawl4ai
import os
from pathlib import Path
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter

async def main():

    # Create the output directory if it doesn't exist
    output_dir = Path("onestop_content")
    output_dir.mkdir(exist_ok=True)
    
    browser_config = BrowserConfig()  
    deep_crawl_strategy = crawl4ai.BFSDeepCrawlStrategy(
        max_depth=1, 
        max_pages=116 
    )
    
    # Create markdown generator with content filtering for "fit" markdown
    markdown_generator = DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(threshold=0.48, threshold_type="fixed")
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun(
            url="https://onestop.fiu.edu",
            config=CrawlerRunConfig(
                deep_crawl_strategy=deep_crawl_strategy,
                markdown_generator=markdown_generator,
                cache_mode=CacheMode.BYPASS  # Skip cache for fresh results
            )
        )
        
            
        print(f"Crawled {len(results)} pages")
        
        # Save each page's markdown to a separate file
        for i, result in enumerate(results):
            if hasattr(result, 'url') and result.url:
                
                url_path = result.url.replace("https://", "").replace("http://", "")
                url_path = url_path.replace("/", "_").replace(".", "_")
                filename = f"{i+1:03d}_{url_path[:50]}.md"  # Limit filename length
            else:
                filename = f"page_{i+1:03d}.md"
                
            filepath = output_dir / filename
            
            # Save fit markdown
            with open(filepath, "w", encoding="utf-8") as f:
                if hasattr(result, 'markdown') and hasattr(result.markdown, 'fit_markdown'):
                    f.write(result.markdown.fit_markdown)
                elif hasattr(result, 'markdown'):
                    f.write(str(result.markdown))
                else:
                    f.write(f"No markdown content available for {result.url if hasattr(result, 'url') else 'unknown page'}")
            
            print(f"Saved page {i+1} to {filepath}")
            
            # Print stats
            if i == 0 and hasattr(result, 'markdown') and hasattr(result.markdown, 'raw_markdown'):
                print("\nFirst page stats:")
                print(f"Raw markdown length: {len(result.markdown.raw_markdown)}")
                print(f"Fit markdown length: {len(result.markdown.fit_markdown)}")
                print(f"Preview: {result.markdown.fit_markdown[:300]}...")
        
        print(f"\nAll content saved to {output_dir.absolute()} directory")

if __name__ == "__main__":
    asyncio.run(main())
