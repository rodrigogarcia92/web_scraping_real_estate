import pandas as pd
import re
import requests
from bs4 import BeautifulSoup

# Apartment Catalog to scrape
apt_data = pd.read_csv('F:/Rodrigo/Antiguo Escritorio/Rodrigo/Cursos y Proyectos/Data Projects/Web Scrapping/Resources/apartment_list.csv', header=0)
apt_columns = apt_data.columns.tolist()
apt_data.columns = apt_columns[1:] + ['XX']

# Extra requirements
address_info = apt_data.iloc[:, :2]
address_list = apt_data.index.tolist()
color_status_dict = {'pending': "#ec3f27", 'off_market': "#0b68bd", 'for_sale': "#067741"}

# Scrape method using requests and BeautifulSoup, without using Selenium
data_list = []

for address in address_list:
    city = address_info.loc[address, 'City']
    state = address_info.loc[address, 'State']

    # Google search URL
    google_url = f"https://www.google.com/search?q={address} {city} {state}"
    google_search = requests.get(google_url)
    google_soup = BeautifulSoup(google_search.content, 'html.parser')

    url_pattern = re.compile(r'https://www\.redfin\.com/[^\s&]+')
    google_soup_str = str(google_soup)
    url_match = url_pattern.findall(google_soup_str)

    # Extracting wanted data
    if url_match:
        url_match = url_match[0]
        response = requests.get(url_match)
        soup = BeautifulSoup(response.content, "html.parser")

        # Extracting color code from html code
        pattern_color = r'ListingStatusBannerSection--statusDot" style="background-color:(#[0-9a-fA-F]+)"'
        text = str(soup)
        match_color = re.search(pattern_color, text)

        if match_color:
            color_code = match_color.group(1)
        else:
            color_code = None

        # Initializing data to None
        estimated_price = None
        sold_info = None
        sale_date = None

        # Determining which data to extract based on the color_code
        if color_code in [color_status_dict['pending'], color_status_dict['for_sale']]:
            # If the color is pending or for_sale, extract estimated_price only
            price_pattern = re.compile(r'<div class="price">(\$[0-9,]+)</div>')
            match = price_pattern.search(str(soup))
            if match:
                estimated_price = match.group(1)
            else:
                # If no match, find any $[0-9,]{5:} pattern and extract that price
                price_pattern_alt = re.compile(r'(\$[0-9,]{5,})')
                match_alt = price_pattern_alt.search(str(soup))
                if match_alt:
                    estimated_price = match_alt.group(1)
        elif color_code == color_status_dict['off_market']:
            # If the color is off_market, extract estimated_price, sold_info, and sale_date
            price_pattern = re.compile(r'<div class="price">(\$[0-9,]+)</div>')
            match = price_pattern.search(str(soup))
            if match:
                estimated_price = match.group(1)
            else:
                # If no match, find any $[0-9,]{5:} pattern and extract that price
                price_pattern_alt = re.compile(r'(\$[0-9,]{5,})')
                match_alt = price_pattern_alt.search(str(soup))
                if match_alt:
                    estimated_price = match_alt.group(1)

            # Last Sold Info
            pattern2 = r"sold for (\$[\d,]+) on ((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{1,2}, \d{4})"
            text_elements = soup.find_all(string=True)

            for text_element in text_elements:
                match = re.search(pattern2, text_element)
                if match:
                    sold_info = match.group(1)
                    sale_date = match.group(2)

        interm_list = [address, estimated_price, sold_info, sale_date, color_code]

        # Append data for the current address to the data_list
        data_list.append(interm_list)
    else:
        # Append None values for the address where url_match is not found
        data_list.append([address, None, None, None, None])
        with open('log_data_list.txt', 'w') as file:
            for item in data_list:
                file.write(' '.join(map(str, item)) + '\n')

# Create a DataFrame from the collected data
scrap_df = pd.DataFrame(data_list, columns=['address', 'estimated_price', 'sold_info', 'sale_date', 'color_code'])
scrap_df.set_index('address', inplace=True)

status_color_dict = {v: k for k, v in color_status_dict.items()}
scrap_df['status'] = scrap_df['color_code'].map(status_color_dict)
scrap_df.drop(columns=['color_code'], inplace=True)
scrap_df.head()
scrap_df.to_excel('scrap_df.xlsx', index=True)

print('Work Done')

print('End')