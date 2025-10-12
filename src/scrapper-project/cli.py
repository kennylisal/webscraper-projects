import click

@click.group()
def cli():
    """CLI for running website scrapers."""
    pass

@cli.command()
@click.option('--query', default="", help="Search query")
@click.option('--pages', default=1, type=int, help="Pages to scrape")
@click.option('--output', default="both", type=click.Choice(["terminal", "file", "both"]))
@click.option('--latest', is_flag=True, help="Fetch latest data")
def nyaa_scraper(query, pages : int, output, latest):
    """Run nyaa-scraper"""
    from nyaa.main import run_scraper
    run_scraper(query, pages, output, latest)


if __name__ == "__main__":
    cli()