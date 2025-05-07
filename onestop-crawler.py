import asyncio
from datetime import datetime
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy

async def main():
    config = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=1,
            include_external=False
        ),
        scraping_strategy=LXMLWebScrapingStrategy(),
        verbose=True
    )

    async with AsyncWebCrawler() as crawler:
        # ← This is where the crawling happens
        results = await crawler.arun("https://onestop.fiu.edu", config=config)
        print(f"Crawled {len(results)} pages in total")

        crawl_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        md = []
        md.append(f"# Crawled Pages Report\n")
        md.append(f"**Crawl Date:** {crawl_date}\n")
        md.append(f"**Total Pages Crawled:** {len(results)}\n")
        md.append("---\n")

        for result in results:
            # ← NEW: safely get fit_markdown
            markdown_obj = result.markdown
            if markdown_obj is not None:
                content = markdown_obj.fit_markdown
            else:
                content = "*(no markdown extracted)*"

            word_count = len(content.split())

            md.append(f"## [{result.url}]({result.url})\n")
            md.append(f"**Depth:** {result.metadata.get('depth', 0)}\n")
            md.append(f"**Word Count:** {word_count}\n")
            md.append("### Extracted Content (Fit Markdown):\n")
            md.append(content + "\n")
            md.append("---\n")

        # write out
        with open("crawl_output.md", "w", encoding="utf-8") as f:
            f.writelines(line + "\n" for line in md)

if __name__ == "__main__":
    asyncio.run(main())
