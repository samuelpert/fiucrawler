# FIU Website Crawler

A powerful and configurable web crawler specifically designed for Florida International University (FIU) websites. This tool can efficiently crawl FIU websites using either sitemap-based or deep crawling approaches.

## Project Goal
Provide the ultimate crawler application for FIU websites with efficient crawling capabilities and flexible configuration options.

## Features

- **Dual Crawling Strategies**:
  - **Sitemap-based crawling**: For websites with sitemaps
  - **Deep crawling**: For websites without sitemaps
- **PDF Discovery**: Automatically finds and indexes PDF files
- **Content Filtering**: Adjustable filtering threshold to ensure quality content
- **Error Detection**: Identifies and reports 404 errors and broken links
- **Markdown Output**: Saves all content in well-structured markdown files
- **Command Line Interface**: Easy-to-use CLI with configurable parameters

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/fiu-website-crawler.git
   cd fiu-website-crawler
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

```bash
python main.py SITE_KEY [options]
```

Where `SITE_KEY` is one of the predefined FIU website keys (e.g., "onestop", "dem", "admissions").

### Command Line Options

- `--max-depth INT`: Maximum crawl depth for deep crawling (default: 2, only for sites without sitemaps)
- `--max-pages INT`: Maximum number of pages to crawl (default: 400, only for sites without sitemaps)
- `--threshold FLOAT`: Content filtering threshold between 0-1 (default: 0.48, higher keeps more content)

### Examples

1. Crawl a site with default parameters:
   ```bash
   python main.py onestop
   ```

2. Crawl a site without sitemap with custom depth and page limit:
   ```bash
   python main.py mymajor --max-depth 3 --max-pages 500
   ```

3. Adjust content filtering threshold (works for all sites):
   ```bash
   python main.py admissions --threshold 0.6
   ```

## Available Sites

### Sites with Sitemaps (only use --threshold)
- onestop
- commencement
- admissions
- dasa
- parking
- news
- dem

### Sites without Sitemaps (use all parameters)
- main
- catalog
- athletics
- sas
- campuslabs
- academicworks
- mymajor

## Output

The crawler saves all content to the `fiu_content` directory with the following structure:

```
fiu_content/
├── site_name/
│   ├── 001_page_url.md
│   ├── 002_page_url.md
│   ├── ...
│   └── pdf_index.md (if PDFs were found)
└── site_name_errors/
    └── error_pages.md (if any errors occurred)
```

Each markdown file contains:
- YAML frontmatter with metadata (URL, title, crawl date)
- Page content with proper formatting

## How It Works

1. For sites with sitemaps:
   - Parses the sitemap.xml to get a list of URLs
   - Extracts and indexes PDF files
   - Crawls each URL and processes the content

2. For sites without sitemaps:
   - Uses BFS (Breadth-First Search) deep crawling strategy
   - Respects max depth and page limits
   - Filters content based on the threshold

## Dependencies

This project uses the following key libraries:
- [Crawl4AI](https://docs.crawl4ai.com) - Advanced web crawling capabilities
- Playwright - Browser automation
- HTTPX - Asynchronous HTTP client
- Beautiful Soup - HTML parsing

## Contributors

- PantherSoft Sprinternship Interns