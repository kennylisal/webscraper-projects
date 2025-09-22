from bs4 import BeautifulSoup
import requests
import time
import pandas as pd
from colorama import init, Fore, Back, Style
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
import asyncio
import aiohttp

init(autoreset=True)
headers = {"User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"}

base_main_url = "https://nyaa.si"

def test_connection_to_webpage(url="https://nyaa.si/user/1_Hong?p=100"):
    r = requests.get(url,headers=headers)
    print(r.status_code)
    if 200 <= r.status_code <300:
        print("something")
    soup = BeautifulSoup(r.content,'lxml')
    print(soup.find('tbody'))

def get_html_content(url, max_retries=5, retry_delay=6):
    for attempt in range(max_retries):
        try:
            r = requests.get(url, headers=headers)
            if 200 <= r.status_code <= 299:
                print(Fore.GREEN + f"GET {url} | code: {r.status_code}", end='\n')
                return r.content
            else:
                print(Fore.RED + f"{url} visit declined code: {r.status_code}")
        except requests.RequestException as e:
            print(Fore.RED + f"{url} request failed: {e}")
        
        if attempt < max_retries - 1:
            print(Fore.YELLOW + f"Retrying ({attempt + 1}/{max_retries}) in {retry_delay} seconds...")
            time.sleep(retry_delay)
        else:
            print(Fore.RED + f"Failed to fetch {url} after {max_retries} attempts")
            return None
    return None

def get_rows_element(html,selector):
    soup = BeautifulSoup(html,'lxml')
    content_element = soup.select(selector)
    if content_element == None:
        line_print(Back.RED,"Data Element is not rendered")
        return None
    table_rows = content_element
    return table_rows


        

def extract_nyaa_table_data(page_row_elements):
    data_collection = []
    for rows in page_row_elements:
        cells = rows.select('td')
        temp_data = {
            'category' : cells[0].find('a').get('title'), # type: ignore
            'name' : cells[1].get_text(strip=True),
            'link' : cells[1].find('a').get('href'), # type: ignore
            'magnet_link' : cells[2].find_all('a')[1].get('href'), # type: ignore
            'size' : cells[3].get_text(strip=True),
            'date' : cells[4].get_text(strip=True)
        }
        data_collection.append(temp_data)
    return data_collection

def scrape_user_page_data(base_url,user_url,depth,user_page_data,error_arr):
    for j in range(1,depth+1):
        user_page_url = f"{base_url}{user_url}?p={j}"
        user_page_html = get_html_content(user_page_url) # type: ignore
        if user_page_html is None:
            line_print(Back.RED,f"Continue to page {j+1}, {user_url} html failed to fetch")
            error_arr.append(f"Failed to fetch index page html |  {user_page_url}")
            continue 

        user_page_row_elements = get_rows_element(user_page_html, 'tbody tr')

        if user_page_row_elements is None:
            line_print(Back.RED,f"Continue to page {j+1}, Content Element failed to fetch")
            error_arr.append(f"No rows on index page {user_page_url}")
            continue 
    
        user_page_data[user_url] += extract_nyaa_table_data(user_page_row_elements)
        print(f"{user_page_url} Data Gathered", end='\n\n')
        # print(len(user_page_data[user_url]))
        time.sleep(1)

def scrape_nyaa_user_data(base_url="https://nyaa.si", index_page_traversed_depth=3,user_page_traverse_depth=3,user_page_data={}):
    errors = []
    for i in range(1,index_page_traversed_depth + 1):
        page_query = f"/?p={i}"
        main_page_html = get_html_content(base_url + page_query)
        if main_page_html is None:
            line_print(Back.RED,f"Continue to page {i+1}, index content Element failed to fetch")
            errors.append(f"Failed to fetch index page html | {base_url + page_query}")
            continue 

        line_print(Back.GREEN,f"indexing from {base_url + page_query}")
        table_row_elements = get_rows_element(main_page_html,'tbody tr')
        if table_row_elements is None:
            line_print(Back.RED,f"Continue to page {i+1}, Content Element failed to fetch")
            errors.append(f"No rows on index page {base_url + page_query}")
            continue 
        #
        #first iteration through index page table
        for rows in table_row_elements:
            cells = rows.select('td')
            view_url = base_main_url + str(cells[1].find('a').get('href')) # type: ignore
            view_html = get_html_content(view_url)
            a_element = get_submitter_info_from_view(view_html)
            if a_element is None:
                line_print(Back.BLUE, "submitter is Anonymous, Skipped")
                continue
            # 
            # Visit User page
            user_url = a_element.get("href") # type: ignore
            line_print(Back.YELLOW, f"Visiting User {user_url}")

            if user_url in user_page_data:
                line_print(Back.BLUE, f"{user_url} already exist on dictionary")
                continue
            #
            # iterate through user page for links
            user_page_data[user_url] = []
            scrape_user_page_data(base_main_url,user_url,user_page_traverse_depth,user_page_data,errors)
            time.sleep(1)
        time.sleep(1)

    if errors:
        print(Fore.RED + "Summary of errors:")
        for err in errors:
            print(err)
    
    return user_page_data



#gather all entry on index and info from its /view
def scrape_index_page(base_url="https://nyaa.si/?p=", page_traversed=5):
    flatened_data = []
    for i in range(1,page_traversed+1):
        main_page_html = get_html_content(f"{base_url}{i}")
        table_row_elements = get_rows_element(main_page_html,'tbody tr')
        flatened_data += extract_nyaa_table_data(table_row_elements)
        line_print(Back.GREEN,f"{base_url}{i} data successfully scraped")
        time.sleep(1)
    df = pd.DataFrame(flatened_data)
    print(df.head(100))

def line_print(bg_color, text,end='\n\n'):
    print(bg_color + Style.BRIGHT  + text, end=end)

def generate_nyaa_url(query=None,page=None,filter=None,category=None,path=None):
    # url = "https://nyaa.si/?f=2&c=1_0&q="

    scheme = 'https'
    netloc = 'nyaa.si'


    path = '/'
    if path is not None:
        path = path

    query_dict = {}
    if page is not None:
        query_dict['p'] = [str(page)]
    if query is not None:
        query_dict['q'] = [query]
    if filter is not None:
        query_dict['f'] = [str(filter)]
    if category is not None:
        query_dict['c'] = [str(category)]

    new_query = urlencode(query_dict, doseq=True)

    new_url = urlunparse((scheme, netloc, path, '', new_query, ''))

    return new_url

def get_url_path(url, segment = None):
    # Parse the URL
    parsed_url = urlparse(url)
    # Get the path component
    path = parsed_url.path
    if segment is None:
        return path
    else:
        segments = [segment for segment in path.split('/') if segment]
        return f"/{segments[segment]}"
    # Split the path into segments and take the first non-empty segment
    # segments = [segment for segment in path.split('/') if segment]
    # If there’s at least one segment, return the first one with a leading '/'
    # return f"/{segments[0]}" if segments else '/'
    

def scrape_nyaa_with_query(query=None,filter=None,category=None,page_traverse = 3):
    flatened_data = []
    for i in range(1,page_traverse+1):
        nyaa_url = generate_nyaa_url(query=query, filter=filter, page=i, category=category)
        page_html = get_html_content(nyaa_url)
        table_row_elements = get_rows_element(page_html, 'tbody tr')
        flatened_data += extract_nyaa_table_data(table_row_elements)
        line_print(Back.GREEN,f"{nyaa_url} data successfully scraped")
        time.sleep(1)
    df = pd.DataFrame(flatened_data)
    print(df.head(100))


def extract_nyaa_table_info(html):
    soup = BeautifulSoup(html,'lxml')
    content_element = soup.select('tbody tr')
    if content_element == None:
        line_print(Back.RED,"Data Element is not rendered")
        return None
    table_rows = content_element
    #
    data_collection = []
    for row in table_rows:
        cells = row.select('td')
        temp_data = {
            'category' : cells[0].find('a').get('title'), # type: ignore
            'name' : cells[1].get_text(strip=True),
            'link' : cells[1].find('a').get('href'), # type: ignore
            'magnet_link' : cells[2].find_all('a')[1].get('href'), # type: ignore
            'size' : cells[3].get_text(strip=True),
            'date' : cells[4].get_text(strip=True)
        }
        data_collection.append(temp_data)
    return data_collection

def get_submitter_info_from_view(html):
    try:
        soup = BeautifulSoup(html, 'lxml')
        submitter_element = soup.select('div.row') # type: ignore
        a_element = submitter_element[1].find('a')
        return a_element
    except Exception as e:
        print(Fore.RED+str(e))
        return None

def get_user_link_from_view(html):
    submitter = get_submitter_info_from_view(html)
    if submitter is None:
        line_print(Back.BLUE, "submitter is Anonymous, Skipped")
        return None
    submitter_url = submitter.get("href") # type: ignore
    return submitter_url

    
def extract_nyaa_page_data(html,page_url):
    #kembalikan data -> sesuai jika dia index, /user, /view
    if get_url_path(page_url,0) is '/' or '/user':
        return extract_nyaa_table_info(html)
    elif get_url_path(page_url,0) is '/view':
        return get_user_link_from_view(html)
    line_print(Back.YELLOW, f"path outside of scope encountered, url : {page_url}")
    return None


class AsyncCrawler:
    def __init__(self, base_url, max_concurrency = 5) -> None:
        self.base_url = base_url
        self.page_data = {}
        self.lock = asyncio.Lock()
        self.max_concurrency = max_concurrency
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.session = None

    async def __aenter__ (self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session is not None:
            await self.session.close()
    
    async def add_page_visit(self,url_destination):
        async with self.lock:
            if url_destination in self.page_data:
                line_print(Back.RED, f"url {url_destination} is already on page_data, Skipped!")
                return False
            self.page_data[url_destination] = None
            return True

    async def get_html(self,url):
        try:
            async with self.session.get(url) as response: # type: ignore
                if response.status != 200:
                    print(f"Error: Status {response.status} for {url}")
                    return None
                if 'text/html' not in response.headers.get('Content-Type', ''):
                    print(f"Non-HTML content for {url}")
                    return None
                return await response.text()   
        except aiohttp.ClientError as e:
                print(f"Error fetching {url}: {e}")
                return None
    
    async def crawl_page(self,destination_url):
        is_new = await self.add_page_visit(destination_url)
        if not is_new:
            return
        
        #limit concurency
        async with self.semaphore:
            html = await self.get_html(destination_url)
            if html is None:
                line_print(Back.RED, f"failed to fetch html content, url : {destination_url}")
                async with self.lock:
                    del self.page_data[destination_url]
                return
        
        # page_info -> isinya link yang mau dikunjungi
        page_info = extract_nyaa_page_data(html,destination_url)
        if page_info is None:
            return

        if get_url_path(destination_url,segment=0) is '/view':
            
            user_path = page_info
            user_url = generate_nyaa_url(user_path)
            print(Fore.GREEN, f"Continuing from {destination_url} to {user_url}",end='\n')
            line_print(Back.GREEN, f"added task to crawl {user_url}")
            await self.crawl_page(user_url)
        else: #this is for '/user' and '/'
            async with self.lock:
                nyaa_path = get_url_path(destination_url)
                self.page_data[nyaa_path] = page_info

            new_urls = page_info

            tasks = []
            for url in new_urls:
                line_print(Back.GREEN, f"adding task to crawl link from {destination_url}")
                if generate_nyaa_url() == self.base_url:
                    task = asyncio.create_task(self.crawl_page(url))
                    tasks.append(task)
                    print(Fore.GREEN, f"Added task to crawl {url}",end='\n')
 
            await asyncio.gather(*tasks)

    async def crawl(self):
        await self.crawl_page(self.base_url)
        return self.page_data


async def crawl_site_async(base_url):
    async with AsyncCrawler(base_url,max_concurrency=2) as crawler:
        line_print(Back.GREEN, f"Starting webcrawling with base url : {base_url}")
        page_data = await crawler.crawl()
        return page_data

async def main_async_crawl():
    base_url = ""
    page_datas = await crawl_site_async(base_url)

    for page in page_datas.values():
        print(page['url'])


if __name__ == "__main__":
    print(get_url_path("https://nyaa.si/view/1234234"))