# Scraping Projects

## Project Overview

This repository contains a collection of web scraping scripts designed for various websites and data sources. Each script is tailored to extract specific information efficiently, using asynchronous techniques for performance. The scripts are modular, allowing for easy extension or integration into larger data pipelines.

## Technology Stack

- **Python 3.10+**: Core language for the script.
- **Asyncio and Aiohttp**: For asynchronous, concurrent HTTP requests to improve crawling speed and efficiency.
- **BeautifulSoup**: For parsing HTML and extracting torrent data from Nyaa's tables.
- **Argparse**: For handling command-line arguments and making the script user-friendly.
- **Urllib**: For URL manipulation and pagination.

The script uses non-blocking I/O to handle multiple page fetches simultaneously, respecting a concurrency limit to avoid overwhelming the server.

## Installation and Setup

This script requires Python 3.10 or higher. We recommend using [UV](https://github.com/astral-sh/uv) (a fast Python package manager) for dependency management, similar to `npm` in Node.js.

1. **Install UV** (if not already installed):

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone the Repository**:

   ```
   git clone https://github.com/kennylisal/webscraper-projects.git
   cd <repository-directory>
   ```

3. **Install Dependencies** (equivalent to `npm install`):
   Assuming the project has a `pyproject.toml` or `requirements.txt`, run:

   ```
   uv sync
   ```

   This installs all required packages (e.g., `beautifulsoup4`, `pandas`, `aiohttp`, `colorama`, etc.) into a virtual environment.

4. **Run the Script**: Use `uv run` to execute it within the managed environment (no need to activate a venv manually).

## About Nyaa-Scraper `nyaa-scrape.py`

The `nyaa-crawl.py` script is a specialized web crawler for [Nyaa.si](https://nyaa.si), a popular torrent site focused on anime, manga, and related media. It fetches torrent entries, including details like file names, sizes, seeders, leechers, and magnet links.

Key features:

- **Latest Entries Mode**: Use the `--latest` flag to retrieve the most recent torrents from the site's main page.
- **Search Query Mode**: Provide a search term (e.g., 'bocchi the rock') via the `--query` flag to crawl results matching the query.
- Supports pagination up to a specified number of pages (default: 1).
- Outputs results to the terminal, a CSV file, or both (default: both).

This script is ideal for monitoring new releases or searching for specific anime torrents without manual browsing.

### Usage

Run the script with `uv run nyaa-crawl.py` followed by options. The script supports the following arguments:

- `-q, --query <search-term>`: Search for torrents matching the query (e.g., 'bocchi the rock'). Wrap multi-word queries in quotes.
- `-p, --pages <number>`: Number of pages to crawl (default: 1).
- `-o, --output <method>`: Output format: `terminal` (default), `file` (CSV), or `both`.
- `-l, --latest`: Flag to fetch the latest torrents (no value needed; sets to True if provided).

### Examples

1. **Fetch Latest Torrents**:

   ```
   uv run nyaa-crawl.py --latest -p 2
   ```

   This crawls the first 2 pages of the latest entries on Nyaa.si.

2. **Search with a Query**:
   ```
   uv run nyaa-crawl.py --query 'bocchi the rock' -p 2 -o both
   ```
   This searches for "bocchi the rock", crawls 2 pages, and outputs to both terminal and a CSV file (e.g., `custom-nyaa-report-20250929.csv`).

### Sample Output (Terminal)

The script displays results in a Pandas DataFrame for easy viewing. Here's an example for the query 'bocchi the rock' with 2 pages:

```
                                        page_url                    category  ... leechers completed_download
0        https://nyaa.si?q=bocchi+the+rock&c=1_2  Anime - English-translated  ...        0                101
1        https://nyaa.si?q=bocchi+the+rock&c=1_2  Anime - English-translated  ...        1                224
2        https://nyaa.si?q=bocchi+the+rock&c=1_2  Anime - English-translated  ...        0                263
3        https://nyaa.si?q=bocchi+the+rock&c=1_2  Anime - English-translated  ...        0                271
4        https://nyaa.si?q=bocchi+the+rock&c=1_2  Anime - English-translated  ...       12               1061
..                                           ...                         ...  ...      ...                ...
145  https://nyaa.si?q=bocchi+the+rock&c=1_2&p=2  Anime - English-translated  ...        0               1238
146  https://nyaa.si?q=bocchi+the+rock&c=1_2&p=2  Anime - English-translated  ...        0                508
147  https://nyaa.si?q=bocchi+the+rock&c=1_2&p=2  Anime - English-translated  ...        0               5787
148  https://nyaa.si?q=bocchi+the+rock&c=1_2&p=2  Anime - English-translated  ...        0                415
149  https://nyaa.si?q=bocchi+the+rock&c=1_2&p=2  Anime - English-translated  ...        0                155
```

### CSV Output

If `--output` is set to `file` or `both`, results are saved to a timestamped CSV file (e.g., `nyaa-report-20250929.csv` or `custom-nyaa-report-20250929.csv`). The file includes columns like `page_url`, `category`, `file_name`, `link`, `magnet_link`, `size`, `date`, `seeders`, `leechers`, and `completed_download`.

### How It Works

1. **Argument Parsing**: Uses `argparse` to handle CLI inputs.
2. **URL Generation**: Builds Nyaa URLs dynamically based on query or latest mode.
3. **Asynchronous Crawling**: Uses `asyncio` and `aiohttp` to fetch pages concurrently, with a semaphore to limit requests (default: 3).
4. **Data Extraction**: Parses HTML with BeautifulSoup to extract torrent tables or user links.
5. **Pagination and Navigation**: Automatically handles next pages and follows view/user links up to the max depth.
6. **Output**: Displays via Pandas in terminal and/or exports to CSV.

### Limitations

- **Rate Limiting**: Nyaa.si may block excessive requests; the script includes a small delay (0.2s) but use responsibly to avoid IP bans.
- **Concurrency**: Limited to 3 simultaneous requests by default to prevent overload; adjust on the paramater code if needed.
- **Error Handling**: Logs errors to terminal; no retries implemented (add if required).
- **Scope**: Focused on anime torrents (category 1_2 by default); customize for other categories.
- **Dependencies**: Requires internet access; no offline mode.
