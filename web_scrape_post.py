from selenium import webdriver
import time
import pandas as pd
import numpy as np
pd.set_option('display.max_columns', None)

# open blank browser
driver = webdriver.Chrome()

# navigate to a url
url = 'https://www.zappos.com/'
driver.get(url)
time.sleep(3)

# find search bar, clear, and enter search text for item
search_bar = driver.find_element_by_xpath("//form[@class='ff']//input[@id='searchAll']")
search_bar.clear()
search_bar.send_keys('holiday gifts')
time.sleep(5)

# find and click 'search' button
search_btn = driver.find_element_by_xpath("//form[@class='ff']"
                                          "//button[@type='submit']")
search_btn.click()
time.sleep(7)

# find and click "$100 & Under" tile
gifts_under_100 = driver.find_element_by_xpath("//div[@class='h_markdown']"
                                               "//p[@class='h_hatch-element--p h_hatch-element--body-1 h_markdown__p']"
                                               "//a[@class='h_hatch-element--a ez_image-link ez_image-link']"
                                               "[@aria-label='image Shop $100 & Under']")

gifts_under_100.click()
time.sleep(3)

# step scroll to bottom to load all images
for i in range(35):
       driver.execute_script("window.scrollBy(0, 900)")
       time.sleep(1)

# # scroll straight to bottom
# driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

# get all product info: brand, product name, price, and product url
product_info = driver.find_elements_by_xpath("//div[@class='h_quick-shop-style-tile']"
                                             "//article[@class='h_hatch-style-tile']"
                                             "//a[@class='h_hatch-element--a h_hatch-style-tile__link']")

product_desc = []
product_urls = []

for info in product_info:
    product_desc.append(info.text.split('\n'))
    product_urls.append(info.get_attribute("href"))

# get product image url and name
product_image = driver.find_elements_by_xpath("//div[@class='h_quick-shop-style-tile']"
                                              "//article[@class='h_hatch-style-tile']"
                                              "//a[@class='h_hatch-element--a h_hatch-style-tile__link']"
                                              "//div[@class='h_hatch-style-tile__image']"
                                              "//div[@class='h_media h_media--3x4']"
                                              "//span[@class='h_media__container']"
                                              "//span[@class='h_media__image-container']"
                                              "//img[@class='h_media__image h_media__image--loaded']")

product_image_url = []
product_image_alt = []

for image in product_image:
    product_image_url.append(image.get_attribute("src"))
    product_image_alt.append(image.get_attribute("alt"))

# data cleaning
""" this section is taking the output of our scraper and converting it to a pandas
    dataframe as well as some cleaning and preparing the data"""

# create pandas dataframe from the above lists
product_desc_df = pd.DataFrame(product_desc, columns=['brand', 'product_name', 'price'])
product_desc_df['product_url'] = product_urls
product_desc_df['product_image_url'] = product_image_url
product_desc_df['product_image_alt'] = product_image_alt

# remove '$' character from price
product_desc_df['price'] = product_desc_df['price'].str.replace('$', '')

# split price column to see price and sale price
product_desc_df[['price_1', 'price_2']] = product_desc_df['price'].str.split('MSRP ', expand=True)

# convert columns to numeric
product_desc_df[['price_1', 'price_2']] = product_desc_df[['price_1', 'price_2']].\
                                                                                apply(pd.to_numeric, errors='coerce')
# add sale flag
product_desc_df['on_sale_flag'] = product_desc_df['price_2'].apply(lambda x: 1 if x is not None else 0)

# add sale price
product_desc_df['sale_price'] = np.where(product_desc_df['on_sale_flag']==1, product_desc_df['price_1'], 0)

# add msrp price
product_desc_df['msrp_price'] = np.where(product_desc_df['price_2'].isnull(), product_desc_df['price_1'],
                                         product_desc_df['price_2'])

# percent off amount
product_desc_df['sale_perc_off'] = \
    np.round(np.where(product_desc_df['sale_price'] > 0,
             (1 - (product_desc_df['sale_price'] / product_desc_df['msrp_price'])) * 100, 0), 0)

# select final columns
final_cols = ['brand', 'product_name', 'product_url', 'product_image_url',
              'on_sale_flag', 'sale_price', 'msrp_price', 'sale_perc_off']

# final dataframe
final_shopping_df = product_desc_df[final_cols]

# save out final shopping list as csv
final_shopping_df.to_csv('~/final_shopping_df.csv', index=False)


