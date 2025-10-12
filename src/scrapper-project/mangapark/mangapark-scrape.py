import aiohttp
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode, quote
from requests_html import HTMLSession,AsyncHTMLSession
from playwright.async_api import async_playwright
from colorama import init, Fore, Back, Style
init(autoreset=True)

def generate_mangapark_url(query=None,page=None,path=''):
    scheme = 'https'
    netloc = 'mangapark.io'

    query_dict = {}
    if query is not None:
        query_dict['word'] = [str(query)]
    if page is not None:
        query_dict['p'] = [page]

    new_query = urlencode(query_dict, quote_via=quote)

    new_url = urlunparse((scheme, netloc, path, '', new_query, ''))

    return new_url


def line_print(bg_color, text,end='\n\n'):
    print(bg_color + Style.BRIGHT  + text, end=end)


class AsyncScraper:
    def __init__(self, query:str, max_concurrency:int):
        self.page_datas = {}
        self.search_query = query
        self.lock = asyncio.Lock()
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.errors = []
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session is not None:
            await self.session.close()

    # this will return list of title and link from query (default : 5 title)
    async def get_manga_titles(self,query):
        try:
            line_print(Back.YELLOW, f"Searching mangapark with query = {query}")
            url = generate_mangapark_url(query=query,path='search')
            # print(f"search url : {url}")
            html = await self.get_html(url)
            soup = BeautifulSoup(html,'lxml')
            title_elements = soup.select('div[q\\:key="jp_1"] h3 a') # type: ignore
            # 
            result = []
            for title_element in title_elements:
                obj = {
                    title_element.get_text(strip=True) : generate_mangapark_url(path=title_element['href']) # type: ignore
                }
                # print(obj)
                result.append(obj)
            if len(result) == 0:
                raise Exception("There is no manga title matching the query")
            return result
        except Exception as e:
            raise e

    #get html from an url
    async def get_html(self,url):
        session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
        try:
            async with session.get(url) as response: # type: ignore
                if response.status != 200:
                    print(f"Error: Status {response.status} for {url}")
                    raise Exception(f"Error: Status {response.status} for {url}")
                if 'text/html' not in response.headers.get('Content-Type', ''):
                    print(f"Non-HTML content for {url}")
                    raise Exception(f"Non-HTML content for {url}")
                return await response.text()   
        except aiohttp.ClientError as e:
                print(f"Error fetching {url}: {e}")
                raise e
        finally:
            await session.close()

    # get list of volumes from a title 
    async def get_list_of_volume(self,url):
        try:
            html = await self.get_html(url)
            soup = BeautifulSoup(html,'lxml')
            table_datas = soup.select('a.link-hover.link-primary.visited\\:text-accent')
            list_of_volume = {}
            ctr = 0 
            for data in table_datas:
                list_of_volume[data.get_text(strip=True)] = data['href']
                ctr += 1
            # print(list_of_volume)
            return list_of_volume,ctr
        except Exception:
            # print(f"Element of manga volume is not exist on {url}")
            raise Exception(f"Element of manga volume is not exist on {url}")

    async def get_chapter_data(self,url, chapter_name ,max_retries = 6):
        line_print(Back.BLUE, f"Starting to scrape {chapter_name} from {url}")
        for i in range(0, max_retries):
            try:
                print(f"attemp {i + 1} to scrape {chapter_name}")
                async with self.semaphore:
                    html = await self.render_and_get_html(url,i)
                soup = BeautifulSoup(html, 'lxml') # type: ignore
                main = soup.find('main')
                img_urls = [img['src'] for img in main.find_all('img')] # type: ignore
                # print(img_urls) 
                line_print(Back.GREEN, f"Success scrape data from {chapter_name} == {url}")
                return img_urls
            except Exception as e:
                # print(f"unexpected error on attemp {i + 1} on {url} | {e}")
                print(e)
                await asyncio.sleep(1)
    
        raise Exception(f"failed to load {url} after {max_retries} tries")

    async def render_and_get_html(self, url, counter):
        browser = None
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, timeout=8500)
                # we could use for wait an element to appear or
                # Alternatively, wait for network to be idle (no requests for 500ms)
                # await page.wait_for_load_state('networkidle')
                await page.wait_for_selector(selector='div[data-name="image-item"]', timeout=6500)
                print("ternyata hasilnya ada ji")
                html = await page.content()
                return html
        except TimeoutError as e:
            raise Exception(f"{counter + 1} attempt timed out, trying again to render : {url}")

        except Exception as e:
            raise Exception(f"unexpected error redering {url}\n{e}")

        finally:
            if browser is not None:
                await browser.close()        

    async def scrape_chapter_page(self, chapter_name,url_path):
        try:
            chapter_url = generate_mangapark_url(path=url_path)
            chapter_data = await self.get_chapter_data(chapter_url, chapter_name)
            async with self.lock:
                self.page_datas[chapter_name] = chapter_data
        except Exception:
            # raise Exception(f"error when trying to scrape {url_path}")
            line_print(Back.RED, f"error when trying to scrape {url_path}")
            async with self.lock:
                self.page_datas[chapter_name]


    async def start_scrape(self,title_url):
        try:
            # limiter
            max_volume_scraped = 10
            volume_scrape_ctr = 0
            # 
            # search_url : list[dict] = await self.get_manga_titles(self.search_query)
            main_url = title_url
            line_print(Back.GREEN,f"Manga target url : {main_url}")
            # print(main_url)
            list_of_volume, volume_count = await self.get_list_of_volume(main_url)
            print(Fore.GREEN + f"Obtained {volume_count} chapters")
            # disini bikin asyncio task
            async_tasks = []
            for key,value in list_of_volume.items():
                # print(value)
                new_task = asyncio.create_task(self.scrape_chapter_page(key,value))
                async_tasks.append(new_task)

                volume_scrape_ctr += 1
                if max_volume_scraped < volume_scrape_ctr:
                    break
            await asyncio.gather(*async_tasks)
            return self.page_datas
        except Exception as e:
            # raise(e)
            self.errors.append(e)
    
    async def testing_ground(self):
        result = await self.scrape_chapter_page("chaprt1","/title/54184-en-domestic-girlfriend/2469848-ch-277")
        return self.page_datas

def get_and_check_index(number, number_of_element):
    try:
        number_choice = int(number)
        number_choice -= 1
        if number_choice+1 > number_of_element:
            raise Exception(f"[{number}] is out of bound (available only {number_of_element})")
        return number_choice
    except ValueError:
        raise Exception("Input suppose to be a number")

async def main():
    async with AsyncScraper("domestic na", 5) as scraper:
        try:
            query = input("Enter your search query: ").strip()
            list_of_titles : list[dict] = await scraper.get_manga_titles(query)
            ctr = 1
            print("\nHere are some choices based on your query:")
            for item in list_of_titles:
                print( f"[{ctr}] {list(item.keys())[0]}")
                ctr +=1
            number_choice = input("Enter choice of number (only number): ").strip()
            number_choice = get_and_check_index(number_choice,ctr)
            
            url = list(list_of_titles[number_choice].values())[0]
            # print(url)
            result = await scraper.start_scrape(url)
            # result = await scraper.testing_ground()
        except Exception as e:
            raise(e)

    

if __name__ == "__main__":
    asyncio.run(main())