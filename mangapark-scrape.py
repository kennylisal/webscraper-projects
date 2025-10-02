import aiohttp
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode, quote
from requests_html import HTMLSession,AsyncHTMLSession
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

# this will return list of title and link from query (default : 5 title)
async def get_manga_titles(query):
    try:
        url = generate_mangapark_url(query=query,path='search')
        print(url)
        html = await get_html(url)
        soup = BeautifulSoup(html,'lxml')
        results = soup.select('div[q\\:key="jp_1"] h3 a') # type: ignore
        for i in range(0,5):
            print({
                results[i].get_text(strip=True) : generate_mangapark_url(path=results[i]['href']) # type: ignore
            })
    except Exception as e:
        raise e
    
async def get_list_of_volume(url):
    html = await get_html(url)
    soup = BeautifulSoup(html,'lxml')
    table_datas = soup.select('a.link-hover.link-primary.visited\\:text-accent')
    list_of_volume = {}
    for data in table_datas:
        list_of_volume[data.get_text(strip=True)] = data['href']
    # print(list_of_volume)
    return list_of_volume
    
async def get_chapter_data(url):
    # html = await get_html(url)
    # soup = BeautifulSoup(html,'lxml')
    # manga_panel_main = soup.find('main')
    # print(manga_panel_main)
    # list_of_image = manga_panel_main.find_all('img') # type: ignore
    # print(list_of_image)
    session = AsyncHTMLSession()
    r = await session.get(url) # type: ignore
    page = await r.html.arender() # type: ignore
    test = page.find('div[data-name\\:"image-item"]')
    print(test)

    
async def main():
    html = await get_html("https://mangapark.io/search?word=domestic")
    if html is None:
         return
    soup = BeautifulSoup(html,'lxml')
    test = soup.select_one('div[q\\:key="jp_1"] h3 a').get('href')
    print(test) # type: ignore
    # titles = 

if __name__ == "__main__":
    # asyncio.run(main())
    # print(generate_mangapark_url(query="domestic na", path="search"))
    # asyncio.run(get_list_of_volume("https://mangapark.io/title/388604-en-housekeeper-in-a-dungeon"))
    asyncio.run(get_chapter_data("https://mangapark.io/title/54184-en-domestic-girlfriend/2469848-ch-277"))
