# headers = {"User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"}

# base_main_url = "https://nyaa.si"

# def test_connection_to_webpage(url="https://nyaa.si/user/1_Hong?p=100"):
#     r = requests.get(url,headers=headers)
#     print(r.status_code)
#     if 200 <= r.status_code <300:
#         print("something")
#     soup = BeautifulSoup(r.content,'lxml')
#     print(soup.find('tbody'))

# def get_html_content(url, max_retries=5, retry_delay=6):
#     for attempt in range(max_retries):
#         try:
#             r = requests.get(url, headers=headers)
#             if 200 <= r.status_code <= 299:
#                 print(Fore.GREEN + f"GET {url} | code: {r.status_code}", end='\n')
#                 return r.content
#             else:
#                 print(Fore.RED + f"{url} visit declined code: {r.status_code}")
#         except requests.RequestException as e:
#             print(Fore.RED + f"{url} request failed: {e}")
        
#         if attempt < max_retries - 1:
#             print(Fore.YELLOW + f"Retrying ({attempt + 1}/{max_retries}) in {retry_delay} seconds...")
#             time.sleep(retry_delay)
#         else:
#             print(Fore.RED + f"Failed to fetch {url} after {max_retries} attempts")
#             return None
#     return None

# def get_rows_element(html,selector):
#     soup = BeautifulSoup(html,'lxml')
#     content_element = soup.select(selector)
#     if content_element == None:
#         line_print(Back.RED,"Data Element is not rendered")
#         return None
#     table_rows = content_element
#     return table_rows


        

# def extract_nyaa_table_data(page_row_elements):
#     data_collection = []
#     for rows in page_row_elements:
#         cells = rows.select('td')
#         temp_data = {
#             'category' : cells[0].find('a').get('title'), # type: ignore
#             'name' : cells[1].get_text(strip=True),
#             'link' : cells[1].find('a').get('href'), # type: ignore
#             'magnet_link' : cells[2].find_all('a')[1].get('href'), # type: ignore
#             'size' : cells[3].get_text(strip=True),
#             'date' : cells[4].get_text(strip=True)
#         }
#         data_collection.append(temp_data)
#     return data_collection

# def scrape_user_page_data(base_url,user_url,depth,user_page_data,error_arr):
#     for j in range(1,depth+1):
#         user_page_url = f"{base_url}{user_url}?p={j}"
#         user_page_html = get_html_content(user_page_url) # type: ignore
#         if user_page_html is None:
#             line_print(Back.RED,f"Continue to page {j+1}, {user_url} html failed to fetch")
#             error_arr.append(f"Failed to fetch index page html |  {user_page_url}")
#             continue 

#         user_page_row_elements = get_rows_element(user_page_html, 'tbody tr')

#         if user_page_row_elements is None:
#             line_print(Back.RED,f"Continue to page {j+1}, Content Element failed to fetch")
#             error_arr.append(f"No rows on index page {user_page_url}")
#             continue 
    
#         user_page_data[user_url] += extract_nyaa_table_data(user_page_row_elements)
#         print(f"{user_page_url} Data Gathered", end='\n\n')
#         # print(len(user_page_data[user_url]))
#         time.sleep(1)

# def scrape_nyaa_user_data(base_url="https://nyaa.si", index_page_traversed_depth=3,user_page_traverse_depth=3,user_page_data={}):
#     errors = []
#     for i in range(1,index_page_traversed_depth + 1):
#         page_query = f"/?p={i}"
#         main_page_html = get_html_content(base_url + page_query)
#         if main_page_html is None:
#             line_print(Back.RED,f"Continue to page {i+1}, index content Element failed to fetch")
#             errors.append(f"Failed to fetch index page html | {base_url + page_query}")
#             continue 

#         line_print(Back.GREEN,f"indexing from {base_url + page_query}")
#         table_row_elements = get_rows_element(main_page_html,'tbody tr')
#         if table_row_elements is None:
#             line_print(Back.RED,f"Continue to page {i+1}, Content Element failed to fetch")
#             errors.append(f"No rows on index page {base_url + page_query}")
#             continue 
#         #
#         #first iteration through index page table
#         for rows in table_row_elements:
#             cells = rows.select('td')
#             view_url = base_main_url + str(cells[1].find('a').get('href')) # type: ignore
#             view_html = get_html_content(view_url)
#             a_element = get_submitter_info_from_view(view_html)
#             if a_element is None:
#                 line_print(Back.BLUE, "submitter is Anonymous, Skipped")
#                 continue
#             # 
#             # Visit User page
#             user_url = a_element.get("href") # type: ignore
#             line_print(Back.YELLOW, f"Visiting User {user_url}")

#             if user_url in user_page_data:
#                 line_print(Back.BLUE, f"{user_url} already exist on dictionary")
#                 continue
#             #
#             # iterate through user page for links
#             user_page_data[user_url] = []
#             scrape_user_page_data(base_main_url,user_url,user_page_traverse_depth,user_page_data,errors)
#             time.sleep(1)
#         time.sleep(1)

#     if errors:
#         print(Fore.RED + "Summary of errors:")
#         for err in errors:
#             print(err)
    
#     return user_page_data



# #gather all entry on index and info from its /view
# def scrape_index_page(base_url="https://nyaa.si/?p=", page_traversed=5):
#     flatened_data = []
#     for i in range(1,page_traversed+1):
#         main_page_html = get_html_content(f"{base_url}{i}")
#         table_row_elements = get_rows_element(main_page_html,'tbody tr')
#         flatened_data += extract_nyaa_table_data(table_row_elements)
#         line_print(Back.GREEN,f"{base_url}{i} data successfully scraped")
#         time.sleep(1)
#     df = pd.DataFrame(flatened_data)
#     print(df.head(100))

# def scrape_nyaa_with_query(query=None,filter=None,category=None,page_traverse = 3):
#     flatened_data = []
#     for i in range(1,page_traverse+1):
#         nyaa_url = generate_nyaa_url(query=query, filter=filter, page=i, category=category)
#         page_html = get_html_content(nyaa_url)
#         table_row_elements = get_rows_element(page_html, 'tbody tr')
#         flatened_data += extract_nyaa_table_data(table_row_elements)
#         line_print(Back.GREEN,f"{nyaa_url} data successfully scraped")
#         time.sleep(1)
#     df = pd.DataFrame(flatened_data)
#     print(df.head(100))
