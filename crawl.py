from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Playwright

def normalize_url(input_url):
    try:
        # Parse the URL into components
        parsed_url = urlparse(input_url)
        
        # Remove scheme (set to empty)
        scheme = ''
        
        # Convert netloc (domain) to lowercase
        netloc = parsed_url.netloc.lower()
        
        # Remove trailing slashes from path
        path = parsed_url.path.rstrip('/')
        
        # Use original query (no sorting, preserves order)
        query = parsed_url.query
        
        # Remove fragment (anything after #)
        fragment = ''
        
        # Reconstruct the normalized URL
        normalized_url = urlunparse((scheme, netloc, path, parsed_url.params, query, fragment))
        
        # Strip leading, remove // from http://
        normalized_url = normalized_url.lstrip('//')
        
        return normalized_url
    
    except ValueError:
        # Return None for invalid URLs
        return None

def get_h1_from_html_debug(html_input):
    soup = BeautifulSoup(html_input,'html.parser')
    result = soup.find('h1').get_text()
    print(result)

def get_first_paragraph_from_html(html_input):
    soup = BeautifulSoup(html_input,'html.parser')
    result = soup.find('p').get_text()
    print(result)



def simple_normalize_url_debug():
    urls = [
    "http://Example.com/path/?b=2&a=1#section",
    "https://www.example.com/path//",
    "example.com",
    "ftp://example.com/path/?a=1",
    "invalid_url"
    ]

    for url in urls:
        normalized = normalize_url(url)
        print(f"Original : {url}\nNormalized : {normalized}\n")

html_doc = """<html>
<body>
<h1>Welcome to Boot.dev</h1>
<main>
    <p>Learn to code by building real projects.</p>
    <p>This is the second paragraph.</p>
    <a href="https://blog.boot.dev">Go to Boot.dev</a>
    <img src="/logo.png" alt="Boot.dev Logo" />
</main>
</body>
</html>"""

if __name__ == "__main__":
    test_has_title()