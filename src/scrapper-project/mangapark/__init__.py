from .main import run_scraper  # Adjust names to match your refactor

# Expose CSV reporter
# from .nyaa_csv_report import write_csv_report

# Optional: Any shared init (e.g., import colorama globally if needed)
# from colorama import init

__all__ = ["run_scraper"]