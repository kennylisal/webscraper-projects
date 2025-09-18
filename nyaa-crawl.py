from bs4 import BeautifulSoup
import requests
import time
import pandas as pd

headers = {"User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"}

base_main_url = "https://nyaa.si"
base_view_url = "https://nyaa.si/view/2021023"
base_user_url = "https://nyaa.si/user/Last_Order"

def test_connection_to_webpage(url="https://nyaa.si/user/1_Hong?p=100"):
    r = requests.get(url,headers=headers)
    print(r.status_code)
    if 200 <= r.status_code <300:
        print("something")
    soup = BeautifulSoup(r.content,'lxml')
    print(soup.find('tbody'))

def get_html_content(url):
    r = requests.get(url,headers=headers)
    if 199 > r.status_code > 299:
        print(r.status_code)
        raise Exception(f"{url} visit declined code : {r.status_code}")
    print(f"{url} sucessfully visited code : {r.status_code}")
    return r.content

def get_rows_element(html,selector):
    soup = BeautifulSoup(html,'lxml')
    content_element = soup.select(selector)
    if content_element == None:
        raise Exception("Data Element is not rendered")
    table_rows = content_element
    # print(table_rows[0]) 
    return table_rows

#gather all entry on index and info from its /view
def scrape_index_page(base_url="https://nyaa.si/?p=", page_traversed=5):
    flatened_data = []
    for i in range(1,page_traversed+1):
        main_page_html = get_html_content(f"{base_url}{i}")
        table_row_elements = get_rows_element(main_page_html,'tbody tr')
        for rows in table_row_elements:
            cells = rows.select('td')
            temp_data = {
                'category' : cells[0].find('a').get('title'), # type: ignore
                'name' : cells[1].get_text(strip=True),
                'link' : cells[1].find('a').get('href'), # type: ignore
                'magnet_link' : cells[2].find_all('a')[1].get('href'), # type: ignore
                'size' : cells[3].get_text(strip=True),
                'date' : cells[4].get_text(strip=True)
            }
            flatened_data.append(temp_data)
        print(f"{base_url}{i} data successfully scraped")
        time.sleep(1)
    print(flatened_data[0])
    df = pd.DataFrame(flatened_data)
    print(df.head(100))


def scrape_view_from_index(base_url="https://nyaa.si", index_page_traversed_depth=3,user_page_traverse_depth=3,user_page_data={}):
    main_page_html = get_html_content(base_url)
    table_row_elements = get_rows_element(main_page_html,'tbody tr')
    for rows in table_row_elements:
        cells = rows.select('td')
        view_url = base_main_url + str(cells[1].find('a').get('href')) # type: ignore
        # 
        view_html = get_html_content(view_url)
        soup = BeautifulSoup(view_html, 'lxml')
        submitter_element = soup.select('div.row') # type: ignore
        a_element = submitter_element[1].find('a')
        print({
            "========Index========"
            'name' : a_element.get_text(strip=True), # type: ignore
            'link' : a_element.get("href") # type: ignore
        })
        if a_element != None:
            for i in range(1,user_page_traverse_depth+1):
                user_page_html = get_html_content(f"{base_main_url}{a_element.get("href")}?p={i}") # type: ignore
                user_page_row_elements = get_rows_element(user_page_html, 'tbody tr')
                for user_rows in user_page_row_elements:
                    user_page_cells = user_rows.select('td')
                    print({
                        "============User============"
                        'name' : user_page_cells[1].find('a').get_text(strip=True), # type: ignore
                        'link' : user_page_cells[1].find('a').get('href') # type: ignore
                    })
                time.sleep(1)
        time.sleep(1)


def crawl_website_for_latest_info(base_url, current_url=None, page_data={}):
    print("hello world")

# def crawl_website_for_latest_info(base_url, current_url=None, page_data={}, user_data={}, base_depth=3, user_depth=3):
#     print("hello world")

if __name__ == "__main__":
    scrape_view_from_index()