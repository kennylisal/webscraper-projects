import aiohttp
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode, quote
from requests_html import HTMLSession,AsyncHTMLSession
from playwright.async_api import async_playwright

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

# this will return list of title and link from query (default : 5 title)
async def get_manga_titles(query):
    try:
        url = generate_mangapark_url(query=query,path='search')
        # print(f"search url : {url}")
        html = await get_html(url)
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
        return result
    except Exception as e:
        raise e

#get html from an url
async def get_html(url):
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
async def get_list_of_volume(url):
    try:
        html = await get_html(url)
        soup = BeautifulSoup(html,'lxml')
        table_datas = soup.select('a.link-hover.link-primary.visited\\:text-accent')
        list_of_volume = {}
        for data in table_datas:
            list_of_volume[data.get_text(strip=True)] = data['href']
        # print(list_of_volume)
        return list_of_volume
    except Exception:
        print(f"Element of manga volume is not exist on {url}")

# extract all link from manga page
async def get_chapter_data(url, max_retries = 5):
    max_retries = max_retries
    for i in range(0, max_retries):
        browser = None
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url)

                # we could use for wait an element to appear or
                # Alternatively, wait for network to be idle (no requests for 500ms)
                # await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('div[data-name="image-item"]', timeout=8000)

                html = await page.content()
                
                soup = BeautifulSoup(html, 'lxml')
                main = soup.find('main')
                img_urls = [img['src'] for img in main.find_all('img')] # type: ignore
                # print(img_urls) 
                return img_urls
            except TimeoutError as e:
                print(f"attemp {i + 1} timed out, trying again to render : {url}")
                await asyncio.sleep(1)
            except Exception:
                print(f"unexpected error on attemp {i + 1} on {url}")
                await asyncio.sleep(1)
            finally:
                if browser is not None:
                    await browser.close()
    
    raise Exception(f"failed to load {url} after {max_retries} tries")


async def main():
    search_url : list[dict] = await get_manga_titles("domestic na")
    main_url = list(search_url[0].values())[0] 
    # print(main_url)
    list_of_volume = await get_list_of_volume(main_url)
    path = list(list_of_volume.values())[0] # type: ignore
    chapter_url = generate_mangapark_url(path=path) # type: ignore
    # print(chapter_url)
    final_res = await get_chapter_data(chapter_url)
    print(final_res)


if __name__ == "__main__":
    asyncio.run(main())
    # asyncio.run(get_chapter_data("https://mangapark.io/title/54184-en-domestic-girlfriend/2394832-ch-264"))
    
