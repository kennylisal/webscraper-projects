# Scraping Projects

## Index

- [CLI Interface](#cli-interface)
- [Nyaa Scraper](#nyaa-scraper)
- [Mangapark Scraper](#mangapark-scraper)

## Project Overview

This repository contains a collection of web scraping scripts designed for various websites and data sources. Each script is tailored to extract specific information efficiently, using asynchronous techniques for performance. The scripts are modular, allowing for easy extension or integration into larger data pipelines.

## Technology Stack

- **Python 3.10+**: Core language for all scripts.
- **Asyncio and Aiohttp**: For asynchronous, concurrent HTTP requests to improve crawling speed and efficiency.
- **BeautifulSoup**: For parsing HTML and extracting data from pages.
- **Argparse**: For handling command-line arguments in individual scripts.
- **Click**: For building the unified CLI interface to run scrapers.
- **Urllib**: For URL manipulation and pagination.
- **Playwright** (Mangapark-specific): For browser automation and rendering JavaScript-heavy pages.
- **Colorama**: For colored terminal output.
- **Pandas** (Nyaa-specific): For tabular data display in the terminal.

The scripts leverage non-blocking I/O to handle multiple page fetches simultaneously, with concurrency limits to avoid overwhelming servers.

## Installation and Setup

This script requires Python 3.10 or higher. We recommend using [UV](https://github.com/astral-sh/uv) (a fast Python package manager, similar to `npm` in Node.js) for dependency management.

1. **Install UV** (if not already installed):

   ```bash:disable-run
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone the Repository**:

   ```
   git clone https://github.com/kennylisal/webscraper-projects.git
   cd webscraper-projects
   ```

3. **Install Dependencies** (equivalent to `npm install`):
   Assuming the project has a `pyproject.toml` or `requirements.txt`, run:

   ```
   uv sync
   ```

   This installs all required packages (e.g., `beautifulsoup4`, `pandas`, `aiohttp`, `colorama`, `click`, `playwright`, etc.) into a virtual environment.

4. **Run Scripts**: Use `uv run` to execute them within the managed environment (no need to activate a venv manually). For the CLI, run `uv run cli.py` (or the configured entry point).

## CLI Interface

The project includes a unified Command-Line Interface (CLI) built with the [Click](https://click.palletsprojects.com/) library, which provides a simple way to run multiple scrapers from a single entry point. Click handles subcommands, options, and flags, making it easy to interact with the scrapers without remembering individual script names.

To use the CLI:

- Run `uv run cli.py --help` to see available commands and options.
- Each scraper is exposed as a subcommand (e.g., `nyaa-scraper`).
- Example: `uv run cli.py nyaa-scraper --query "bocchi the rock" --pages 2 --output both`.

Currently supported subcommands:

- `nyaa-scraper`: Runs the Nyaa torrent scraper (see [Nyaa Scraper](#nyaa-scraper) for details).

More subcommands (e.g., for Mangapark) will be added in the future. If running standalone scripts, use `uv run <script-name>.py` directly.

## Nyaa Scraper

The `nyaa-crawl.py` script is a specialized web crawler for [Nyaa.si](https://nyaa.si), a popular torrent site focused on anime, manga, and related media. It fetches torrent entries, including details like file names, sizes, seeders, leechers, and magnet links.

Key features:

- **Latest Entries Mode**: Use the `--latest` flag to retrieve the most recent torrents from the site's main page.
- **Search Query Mode**: Provide a search term (e.g., `--query 'bocchi the rock'`) to crawl results matching the query.
- Supports pagination up to a specified number of pages (default: 1).
- Outputs results to the terminal, a CSV file, or both (default: both).

This script is ideal for monitoring new releases or searching for specific anime torrents without manual browsing.

### Usage

Run the script standalone with `uv run nyaa-crawl.py` followed by options, or via the CLI: `uv run cli.py nyaa-scraper` with the same options.

The script supports the following arguments:

- `-q, --query <search-term>`: Search for torrents matching the query (e.g., 'bocchi the rock'). Wrap multi-word queries in quotes.
- `-p, --pages <number>`: Number of pages to crawl (default: 1).
- `-o, --output <method>`: Output format: `terminal`, `file` (CSV), or `both` (default: both).
- `-l, --latest`: Flag to fetch the latest torrents (no value needed; sets to True if provided).

### Examples

1. **Fetch Latest Torrents** (standalone):

   ```
   uv run nyaa-crawl.py --latest -p 2
   ```

   Or via CLI:

   ```
   uv run cli.py nyaa-scraper --latest --pages 2
   ```

   This crawls the first 2 pages of the latest entries on Nyaa.si.

2. **Search with a Query** (standalone):

   ```
   uv run nyaa-crawl.py --query 'bocchi the rock' -p 2 -o both
   ```

   Or via CLI:

   ```
   uv run cli.py nyaa-scraper --query 'bocchi the rock' --pages 2 --output both
   ```

   This searches for "bocchi the rock", crawls 2 pages, and outputs to both terminal and a CSV file (e.g., `custom-nyaa-report-20251013.csv`).

### CSV Output

If `--output` is set to `file` or `both`, results are saved to a timestamped CSV file (e.g., `nyaa-report-20251013.csv` or `custom-nyaa-report-20251013.csv`). The file includes columns like `page_url`, `category`, `file_name`, `link`, `magnet_link`, `size`, `date`, `seeders`, `leechers`, and `completed_download`.

### How It Works

1. **Argument Parsing**: Uses `argparse` (or Click via CLI) to handle inputs.
2. **URL Generation**: Builds Nyaa URLs dynamically based on query or latest mode.
3. **Asynchronous Crawling**: Uses `asyncio` and `aiohttp` to fetch pages concurrently, with a semaphore to limit requests (default: 3).
4. **Data Extraction**: Parses HTML with BeautifulSoup to extract torrent tables or user links.
5. **Pagination and Navigation**: Automatically handles next pages and follows view/user links up to the max depth.
6. **Output**: Displays via Pandas in terminal and/or exports to CSV.

### Limitations

- **Rate Limiting**: Nyaa.si may block excessive requests; the script includes a small delay (0.2s) but use responsibly to avoid IP bans.
- **Concurrency**: Limited to 3 simultaneous requests by default to prevent overload; adjust in the code if needed.
- **Error Handling**: Logs errors to terminal; no automatic retries.
- **Scope**: Focused on anime torrents (category 1_2 by default); customize for other categories.
- **Dependencies**: Requires internet access; no offline mode.

## Mangapark Scraper

The `mangapark-scrape.py` script is a specialized web crawler for [Mangapark.io](https://mangapark.io), a manga reading site. It interactively searches for manga titles, allows selection, and extracts image URLs from chapters (e.g., for downloading or viewing manga pages).

Key features:

- **Interactive Search**: Prompts for a search query, lists matching titles, and lets the user select one.
- **Chapter Scraping**: Fetches image URLs from up to 10 chapters (volumes) of the selected manga.
- Uses browser rendering for JavaScript-heavy pages to ensure complete data extraction.
- Outputs scraped image URLs to the terminal with colored logging.

This script is ideal for quickly extracting manga chapter images without manual navigation.

### Usage

Run the script with `uv run mangapark-scrape.py`. It is interactive and does not support command-line arguments yet (future integration with the CLI is planned).

Interaction steps:

1. Enter a search query when prompted (e.g., "domestic na").
2. Review the list of matching titles (numbered).
3. Enter the number of your chosen title.
4. The script will automatically scrape chapters and display progress/errors.

### Examples

1. **Basic Run**:

   ```
   uv run mangapark-scrape.py
   ```

   - Prompt: "Enter your search query: " → Enter "domestic na".
   - Displays titles like: "[1] Domestic Girlfriend".
   - Prompt: "Enter choice of number (only number): " → Enter "1".
   - Scrapes chapters and prints image URLs.

### Output

Results are printed to the terminal, including chapter names and lists of image URLs. No file output is implemented yet (e.g., could be extended to save images or JSON).

### How It Works

1. **User Input**: Prompts for query and title selection.
2. **URL Generation**: Builds Mangapark search URLs dynamically.
3. **Asynchronous Crawling**: Uses `asyncio` and `aiohttp` for initial fetches, with a semaphore to limit concurrency (default: 5).
4. **Data Extraction**: Parses HTML with BeautifulSoup to get titles and volumes.
5. **Browser Rendering**: Uses Playwright to render chapter pages (retries up to 6 times) and extract image URLs.
6. **Output**: Logs progress with Colorama; stores data in a dictionary for potential further use.

### Limitations

- **Interactivity Only**: No CLI options yet; must run interactively.
- **Volume Limit**: Scrapes a maximum of 10 chapters to avoid overload; adjust in code.
- **Retries**: Up to 6 attempts per chapter with timeouts; may fail on slow connections.
- **Scope**: Focused on image extraction; does not download images (add if needed).
- **Rate Limiting**: Mangapark may throttle requests; use responsibly.
- **Dependencies**: Requires internet and Playwright browser installation (handled by UV); no offline mode.

```

```
