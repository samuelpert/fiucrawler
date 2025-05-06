from crawl4ai import AsyncWebCrawler
import asyncio

async def generic_crawl(url, scroll=True, ai_extract=True, selectors=None, output_format="markdown"):
    async with AsyncWebCrawler(
        headless=True,
        scroll_page=scroll,
        ai_extract=ai_extract
    ) as crawler:
        result = await crawler.arun(
            url=url,
            selectors=selectors,
        )

        if output_format == "markdown":
            return result.markdown
        elif output_format == "html":
            return result.html
        elif output_format == "json":
            return result.json
        else:
            return "Unsupported format."

# Example usage:
asyncio.run(generic_crawl(
    url="https://example.com",
    scroll=True,
    ai_extract=False,
    selectors={"title": "h1", "description": "p"},
    output_format="json"
))


print(asyncio.run(generic_crawl(url="https://onestop.fiu.edu")))




