from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Playwright, Page
import pandas as pd
headers = {"User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"}

def try_visit_url(page: Page, url, selector):
    try:
        page_response = page.goto(url)
        if page_response != None and page_response.ok and page.url == url:
            page.wait_for_selector(selector, timeout=5000)
            html = page.content()
            print("Subplease schedule successfully visited")   
            return html         
    except Exception as e:
        print(f"Navigation failed: {str(e)}")
        return None

def compile_shows_element_to_flatened_data(shows_element):
    alphanum_index = None
    flatened_shows_data = []
    for element in shows_element: # type: ignore
        if element.get('class') == ['alphanum-category']: # type: ignore
            alphanum_index = element.get_text(strip=True)
            # print(element.get_text(strip=True))
        elif element.get('class') == ['all-shows-link']: # type: ignore
            temp_data = {
                'index': alphanum_index,
                'show_name' : element.get_text(strip=True),
                'show_link' : element.find('a').get('href') # type: ignore
            }
            flatened_shows_data.append(temp_data)
        else:
            print(f"unexpected element encountered {element}")
    return flatened_shows_data

def get_content_elements(html, selector):
    soup = BeautifulSoup(html,features='lxml')
    schedule_table = soup.select_one(selector)
    if schedule_table == None:
        raise Exception("Schedule element is Empty")
    return schedule_table.contents

def compile_flatened_data_from_element(schedule_element):
    day_pointer = None
    schedule_result = []
    for row in schedule_element:
        try:
            if row.get('class') == ['day-of-week']: # type: ignore
                day_pointer = row.get_text(strip=True)
            elif row.get('class') == ['all-schedule-item']: # type: ignore
                td_data_arr = row.find_all('td') # type: ignore
                schedule_info = {
                    'day' : day_pointer,
                    'anime_name' : td_data_arr[0].get_text(strip=True),
                    'release_schedule' : td_data_arr[1].get_text(strip=True),
                    'link_to_page' : td_data_arr[0].find('a').get('href') # type: ignore
                }
                schedule_result.append(schedule_info)
        except Exception as e:
            print(f"Parsing Table Data Error : {str(e)}")  
    return schedule_result

def scrape_shows_data(playwright: Playwright):
    url = 'https://subsplease.org/shows/'
    chromium = playwright.chromium 
    browser = chromium.launch(headless=True)
    page = browser.new_page()
    html = None
    
    html = try_visit_url(page,url,'div.all-shows')

    if html == None:
        print("getting schedule data failed")
    else:
        # shows_element = get_all_shows_section(html)
        shows_element = get_content_elements(html,'div.all-shows')
        flatened_shows_data = compile_shows_element_to_flatened_data(shows_element)
        df = pd.DataFrame(flatened_shows_data)
        print(df.head(100))

    browser.close() 

def scrape_schedule_data(playwright: Playwright):
    url = 'https://subsplease.org/schedule/'
    chromium = playwright.chromium 
    browser = chromium.launch(headless=True)
    page = browser.new_page()
    
    # page.set_extra_http_headers({"User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"})
    html = try_visit_url(page,url,'#full-schedule-table tr:has-text("Monday")')

    if html != None:
        schedule_element = get_content_elements(html,'table#full-schedule-table')
        flatened_data = compile_flatened_data_from_element(schedule_element)
        df = pd.DataFrame(flatened_data)
        print(df)
    else:
        print("getting schedule data failed")

    browser.close()    

if __name__ == "__main__":
    with sync_playwright() as playwright:
        scrape_shows_data(playwright)


# def turn_schedule_table_data_to_objects(schedule_table):
#     day_pointer = None
#     schedule_result = {}
#     for row in schedule_table:
#         try:
#             if row.get('class') == ['day-of-week']: # type: ignore
#                 day_pointer = row.get_text(strip=True)
#                 schedule_result[day_pointer] = []
#             elif row.get('class') == ['all-schedule-item']: # type: ignore
#                 td_data_arr = row.find_all('td') # type: ignore
#                 schedule_info = {
#                     'anime_name' : td_data_arr[0].get_text(strip=True),
#                     'release_schedule' : td_data_arr[1].get_text(strip=True),
#                     'link_to_page' : td_data_arr[0].find('a').get('href') # type: ignore
#                 }
#                 schedule_result[day_pointer].append(schedule_info)
#         except Exception as e:
#             print(f"Parsing Table Data Error : {str(e)}")
#     # print(schedule_result)
#     return schedule_result