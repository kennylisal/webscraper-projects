from bs4 import BeautifulSoup
import pandas as pd
from colorama import init, Fore, Back, Style
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
import asyncio
import aiohttp
import nyaa_csv_report 
import argparse
from datetime import datetime

init(autoreset=True)

def line_print(bg_color, text,end='\n\n'):
    print(bg_color + Style.BRIGHT  + text, end=end)

def generate_nyaa_url(query=None,page=None,filter=None,category=None,path=''):
    scheme = 'https'
    netloc = 'nyaa.si'

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

def add_next_page_url(url, max_page, page=None):
    # Parse the URL into components
    parsed_url = urlparse(url)
    
    # Extract query parameters
    query_dict = parse_qs(parsed_url.query)
    
    # Get current page number or default to 1
    current_page = int(query_dict.get('p', ['1'])[0])
    if current_page > max_page:
        return None

    if page:
        query_dict['p'] = [page]
    else: 
        query_dict['p'] = [str(current_page + 1)]

    
    
    # Encode the updated query parameters
    new_query = urlencode(query_dict, doseq=True)
    
    # Reconstruct the URL with the updated page number
    new_url = urlunparse((
        parsed_url.scheme,
        parsed_url.netloc,
        parsed_url.path,
        parsed_url.params,
        new_query,
        parsed_url.fragment
    ))

    return new_url


def get_url_path(url, segment = None):
    # Parse the URL
    try:
        parsed_url = urlparse(url)
        # Get the path component
        path = parsed_url.path
        if segment is None:
            return path
        else:
            if path == '':
                return ''
            segments = [segment for segment in path.split('/') if segment]
            return f"/{segments[segment]}"
    except Exception:
        line_print(Back.RED , f"url is {url}")
        return False

def safe_parse_int(value):
    try:
        res = int(value)
        return res
    except:
        return 0

def extract_nyaa_table_info(html):
    soup = BeautifulSoup(html,'lxml')
    #check if no result first
    if soup.find('h3',string='No results found'):
        return None
    # 
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
            'file_name' : cells[1].get_text(strip=True),
            'link' : cells[1].find('a').get('href'), # type: ignore
            'magnet_link' : cells[2].find_all('a')[1].get('href'), # type: ignore
            'size' : cells[3].get_text(strip=True),
            'date' : cells[4].get_text(strip=True),
            'seeders' : safe_parse_int(cells[5].get_text(strip=True)),
            'leechers' : safe_parse_int(cells[6].get_text(strip=True)),
            'completed_download' : safe_parse_int(cells[7].get_text(strip=True))
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
    if get_url_path(page_url,0) == '' or get_url_path(page_url,0) == '/' or get_url_path(page_url,0) == '/user':
        return extract_nyaa_table_info(html)
    elif get_url_path(page_url,0) == '/view':
        return get_user_link_from_view(html)
    line_print(Back.YELLOW, f"path outside of scope encountered, url : {page_url}")
    return None



class AsyncScraper:
    def __init__(self, base_url, max_concurrency = 5, max_page_traverse = 3) -> None:
        self.base_url = base_url
        self.page_data = {}
        self.lock = asyncio.Lock()
        self.max_concurrency = max_concurrency
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.session = None
        self.errors = []
        self.max_page = max_page_traverse
        self.page_tasks = {}

    async def __aenter__ (self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session is not None:
            await self.session.close()
    
    async def extract_table_page(self, url_to_crawl, page_num):
        self.page_data[url_to_crawl] = None

        async with self.semaphore:
            html = await self.get_html(url_to_crawl)
            if html is None:
                self.errors.append(f"failed to fetch html content, url : {url_to_crawl}")
                line_print(Back.RED, f"failed to fetch html content, url : {url_to_crawl}")
                async with self.lock:
                    del self.page_data[url_to_crawl]
                return
        
        page_info = extract_nyaa_table_info(html)
        if page_info is None:
            # this mean all the available result are already traversed
            # stop all the asyncio task
            self.errors.append(f"There are no more page to crawl, last url to crawl : {url_to_crawl}")
            async with self.lock:
                for p, t in list(self.page_tasks.items()):
                    if p > page_num and not t.done():
                        t.cancel()
            return
        
        async with self.lock:
            self.page_data[url_to_crawl] = page_info

    async def crawl_custom_query(self):
        tasks = []
        for i in range(1,self.max_page + 1):
            url = add_next_page_url(self.base_url,self.max_page,i)
            task = asyncio.create_task(self.extract_table_page(url, i))
            self.page_tasks[i] = task
            tasks.append(task)
            print(Fore.GREEN + f"Added task to crawl {url}")
        await asyncio.gather(*tasks, return_exceptions=True)

        line_print(Back.GREEN, f"Finish crawling {self.base_url} with max_dept of {self.max_page} pages")

    async def custom_crawl(self):
        await self.crawl_custom_query()
        return self.page_data
    
    async def add_page_visit(self,url_destination):
        if get_url_path(url_destination, 0) == '/view':
            return True
        async with self.lock:
            if url_destination in self.page_data:
                self.errors.append(f"url {url_destination} is already on page_data, Skipped!")
                return False
            print(Fore.GREEN + f"added to page_data {url_destination}")
            self.page_data[url_destination] = None
            return True
        
    async def get_html(self,url):
        await asyncio.sleep(0.2)
        try:
            async with self.session.get(url) as response: # type: ignore
                if response.status != 200:
                    print(f"Error: Status {response.status} for {url}")
                    self.errors.append(f"Error: Status {response.status} for {url}")
                    return None
                if 'text/html' not in response.headers.get('Content-Type', ''):
                    print(f"Non-HTML content for {url}")
                    self.errors.append(f"Non-HTML content for {url}")
                    return None
                return await response.text()   
        except aiohttp.ClientError as e:
                print(f"Error fetching {url}: {e}")
                self.errors.append(f"Error fetching {url}: {e}")
                return None
        
    async def crawl_page(self,url_to_crawl):
        line_print(Back.BLUE, f"start crawling for {url_to_crawl}")
        is_new = await self.add_page_visit(url_to_crawl)
        if not is_new:
            return
        
        #limit concurency
        async with self.semaphore:
            print(Fore.GREEN + f"fetching html from : {url_to_crawl}")
            html = await self.get_html(url_to_crawl)
            if html is None:
                self.errors.append(f"failed to fetch html content, url : {url_to_crawl}")
                line_print(Back.RED, f"failed to fetch html content, url : {url_to_crawl}")
                async with self.lock:
                    del self.page_data[url_to_crawl]
                return
        
        # page_info -> isinya link yang mau dikunjungi
        page_info = extract_nyaa_page_data(html,url_to_crawl)
        if page_info is None:
            return


        if get_url_path(url_to_crawl,segment=0) == '' or get_url_path(url_to_crawl,segment=0) == '/':
            async with self.lock:
                nyaa_path = url_to_crawl
                self.page_data[nyaa_path] = page_info

            new_urls = []
            for item in page_info:
                try:
                    new_urls.append(item['link']) # type: ignore
                except:
                    continue

            tasks = []
            line_print(Back.GREEN, f"adding task to crawl links from {url_to_crawl}")
            ctr = 0
            for url in new_urls:
                if generate_nyaa_url() == self.base_url:
                    view_url = generate_nyaa_url(path=url)
                    task = asyncio.create_task(self.crawl_page(view_url))
                    tasks.append(task)
                    ctr +=1
                    if(ctr > 5):
                        break

            next_page_url = add_next_page_url(self.base_url, self.max_page)

            if next_page_url:
                next_page_task = asyncio.create_task(self.crawl_page(next_page_url))
                tasks.append(next_page_task)
                print(Fore.GREEN, f"Added task to crawl {next_page_task}",end='\n')   

            print(Fore.GREEN + f"Added {len(tasks)} url to crawl")
            await asyncio.gather(*tasks)
        elif get_url_path(url_to_crawl,segment=0) == '/view':
            user_path = page_info
            user_url = generate_nyaa_url(path=user_path) # type: ignore
            print(Fore.GREEN, f"Continuing from {url_to_crawl} to {user_url}",end='\n')
            line_print(Back.GREEN, f"added task to crawl {user_url}")
            await asyncio.gather(*[asyncio.create_task(self.crawl_page(user_url))])
        elif get_url_path(url_to_crawl,segment=0) == '/user': #this is for '/user'
            async with self.lock:
                nyaa_path = url_to_crawl
                self.page_data[nyaa_path] = page_info
            next_page_url = add_next_page_url(url_to_crawl, self.max_page)
            if next_page_url:                    
                print(Fore.GREEN, f"Continuing from {url_to_crawl} to {next_page_url}",end='\n')
                line_print(Back.GREEN, f"added task to crawl {next_page_url}")
                await asyncio.gather(*[asyncio.create_task(self.crawl_page(next_page_url))])

    async def crawl(self):
        await self.crawl_page(self.base_url)
        line_print(Back.GREEN, f"Finish crawling {self.base_url} with max_dept of {self.max_page} pages")
        return self.page_data


async def scrape_nyaa_with_query(base_url, max_pages):
    async with AsyncScraper(base_url,max_concurrency=3, max_page_traverse=max_pages) as crawler:
        line_print(Back.GREEN, f"Starting webcrawling with base url : {base_url}")
        page_data = await crawler.crawl()
        
        # 
        line_print(Back.RED , "Here are the error that occured during crawling : ")
        for error in crawler.errors:
            print(Fore.RED,error)
        # 
        return page_data

async def scrape_nyaa_latest(base_url, max_pages):
    async with AsyncScraper(base_url,max_concurrency=3, max_page_traverse=max_pages) as crawler:
        line_print(Back.GREEN, f"Starting webcrawling with base url : {base_url}")
        page_data = await crawler.custom_crawl()
        # 
        line_print(Back.RED , "Here are the error that occured during crawling : ")
        for error in crawler.errors:
            print(Fore.RED,error)
        # 
        return page_data
    
def display_data_with_panda(data:dict):
    line_print(Back.CYAN,"Here are the crawled data")
    result = []
    for key,values in data.items():
        for value in values:
            result.append(
                {
                    "page_url": key,
                    "category": value.get("category", ""),
                    "file_name": value.get("file_name", ""),
                    "link": value.get("link", ""),
                    "magnet_link": value.get("magnet_link", ""),
                    "size": value.get("size", ""),
                    "date": value.get("date", ""),
                    "seeders": value.get("seeders", 0),
                    "leechers": value.get("leechers", 0),
                    "completed_download": value.get("completed_download", 0)
                }
            )
    df = pd.DataFrame(result)
    print(df.head(250))

def parse_argument():
# Create an ArgumentParser object
    parser = argparse.ArgumentParser(
        description='''A script to crawl and gather data from nyaa :)'''
    )

    parser.add_argument("-q", "--query", type=str,required=False,default="",help="Use quote mark (e.g., 'bocchi the rock')")
    parser.add_argument("-p","--pages", type=int,default=1,required=False,help="Number of pages to process (default: 1)")
    parser.add_argument("-o","--output", type=str,choices=["terminal", "file", "both"], default="both",help="Output method: terminal, csv, or both (default: terminal)")
    parser.add_argument("-l", "--latest", action='store_true', help="Fetch the latest data (default: False)")
    args, unknown = parser.parse_known_args()
    return args
    # Check if -u or --url was provided in the command line
    # url_provided = any(arg in sys.argv for arg in ["-u", "--url"])
    # receiving url_provided -> args, url_provided = parse_argument()
    # return args, url_provided

if __name__ == "__main__":
    # asyncio.run(crawl_site_with_query(, 2))
    # url+query example -> https://nyaa.si/?f=0&c=1_2&q=bocchi+the+rock
    args = parse_argument()
    print(args)
    # print(generate_nyaa_url(query=args.query,filter="1_2"))
    crawl_datas = None
    if args.latest:
        print("masuk latest")
        crawl_datas = asyncio.run(scrape_nyaa_latest("https://nyaa.si",args.pages))
    else:
        print("masuk query")
        base_url = generate_nyaa_url(query=args.query,category="1_2")
        crawl_datas = asyncio.run(scrape_nyaa_with_query(base_url, args.pages))   

    if crawl_datas is None:
        line_print(Back.RED, "Failed to fetch data")
        exit() 
    
    today = datetime.today().strftime("%Y%m%d")
    if args.output == "both":
        display_data_with_panda(crawl_datas)
        name = nyaa_csv_report.write_csv_report(crawl_datas,f"custom-nyaa-report-{today}.csv")
        print(Fore.GREEN + f"data is store on file {name}")
    elif args.output == "csv":
        name = nyaa_csv_report.write_csv_report(crawl_datas,f"nyaa-report-{today}.csv")
        print(Fore.GREEN + f"data is store on file {name}")
    else:
        display_data_with_panda(crawl_datas)
