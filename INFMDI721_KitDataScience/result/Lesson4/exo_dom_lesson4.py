#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 28 11:03:07 2018

@author: macbook
"""

import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import itertools
from multiprocessing.dummy import Pool as ThreadPool 


#%%
def get_ads_url_1page(url_query):
    root = "https://www.lacentrale.fr"

    urls = []
    soup = get_soup(url_query)
    result = soup.find(class_="resultListContainer").find_all(class_="adLineContainer")

    for tag in result:
        if tag.find(class_="linkAd") is None:
            continue
        else:
            urls.append(tag.find(class_="linkAd").attrs["href"])

    url_1_page = list(map(lambda x : root + x, urls))        
    return url_1_page
#%%
def number_pages(url):
    soup = get_soup(url)
    nb_ad = int(soup("span", class_="numAnn")[0].text)
    ads_per_page = 16
    if nb_ad % ads_per_page == 0:
        nb_pages = int(nb_ad / ads_per_page)
    else:
        nb_pages = int(nb_ad / ads_per_page) +1
    return nb_pages

#%%
def build_pages_url(nb_pages=1, car_brand = "RENAULT", car_type = "ZOE", regions = ["PAC", "IDF", "NAQ"]):
    url_pages = [build_1page_url(page, car_brand, car_type, regions) for page in range(nb_pages)]
    return url_pages
#%%
def build_1page_url(page=0, car_brand = "RENAULT", car_type = "ZOE", regions = ["PAC", "IDF", "NAQ"]):
    url_root = "https://www.lacentrale.fr/listing?makesModelsCommercialNames="
    name = car_brand + "%3A" + car_type
    regions_root = "%2C".join(["FR-" + region for region in regions])
    return url_root + name + "&options=&page=" + str(page+1) + "&regions=" + regions_root

#%%
def get_soup(url_page):
    
    res = requests.get(url_page)
    if res.status_code == 200:
#        print("status ok")
        html_doc =  res.text
        soup = BeautifulSoup(html_doc,"html.parser")
    return soup
#%%
def get_infos_car(url_ad):
    soup = get_soup(url_ad)
    print("retrieving " + url_ad)
    # retrieve model
    model_raw = soup.find_all("div", class_ ="versionTxt txtGrey7C sizeC mB10 hiddenPhone")[0].text.strip()
    model = model_raw
    
    # Price
    price_raw = soup.find_all("strong", class_ ="sizeD lH35 inlineBlock vMiddle ")[0].text.strip()
    price = "".join(re.findall('\d',price_raw))
    
    # Phone Number
    phone_raw = soup.find_all("div", class_="phoneNumber1")[0].find_all("span", class_="bold")[0].text.strip()
    phone = " ".join(phone_raw.split(" ")[0].split())
    
    # Year
    year = soup.find_all("ul", class_="infoGeneraleTxt column2")[0].find_all("span")[0].text
    
    # mileage
    km_raw = soup.find_all("ul", class_="infoGeneraleTxt column2")[0].find_all("span")[1].text
    km = km_raw
    
    # Vendor type
    vendor_raw = soup.find_all("div", class_="bold italic mB10")[0].next_element.strip()
    vendor = vendor_raw
    
    info_1_car = pd.Series([model, year, km, price, phone, vendor],
                           index=["model","year","km","price","phone","vendor"])
#    print(info_1_car)
    return info_1_car

#%%

def get_all_ads_url(url_pages):
    url_all_ads = []
    pool = ThreadPool(4) 
    list_url_all_ads = pool.map(get_ads_url_1page, url_pages)
    url_all_ads = list(itertools.chain.from_iterable(list_url_all_ads))
    return url_all_ads


#%%

def collect_all_infos_car(url_all_ads):
    pool = ThreadPool(4) 
    frames = pool.map(get_infos_car, url_all_ads)
    df = pd.DataFrame(frames, columns=["model","year","km","price","phone","vendor"])
    return df

#%%
def clean_data(df):
    r_model = ".*(LIFE|ZEN|INTENS).*"
    df.model = df.model.str.extract(r_model)
    df.year = pd.Series(df.year, dtype='int')
    r_km = "((\d*)\s?(\d*)).*"
    df.km = df.km.str.extract(r_km)
    df.km = list(map("".join, df.km.str.split()))
    df.km = pd.Series(df.km, dtype='int')
    df.price = pd.Series(df.price, dtype='int')
    r_vendor = ".*(Professionnel|Particulier).*"
    df.vendor = df.vendor.str.extract(r_vendor)
    return df
    
    


#%%

car_brand = "RENAULT"
car_type = "ZOE"
regions = ["PAC", "IDF", "NAQ"]

main_url = build_1page_url(0, car_brand, car_type, regions)
pages = number_pages(main_url)
url_pages = build_pages_url(pages, car_brand, car_type, regions)
url_all_ads = get_all_ads_url(url_pages)
df = collect_all_infos_car(url_all_ads)



