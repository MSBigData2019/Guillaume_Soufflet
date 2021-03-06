#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct  9 17:54:02 2018

@author: macbook
"""

# coding: utf-8
import requests
import unittest
from bs4 import BeautifulSoup
import re
import pandas as pd

#page_url = "https://www.reuters.com/finance/stocks/financial-highlights/LVMH.PA"
#res = requests.get(page_url)

#%%
def get_key_figures(companies):
    info = {}
    # TODO Add dictionnary correspondance between Reuters company coding
    # and usual name
    # TODO Add a try on company name and error message to user if not found
    for company in companies:
        info[company] = get_data(company)
    result = pd.DataFrame(info)
    return result
#%%
def get_data(company):
    url = 'https://www.reuters.com/finance/stocks/financial-highlights/'
    res = requests.get(url+company)
    soup = _handle_request_result_and_build_soup(res)
    tags_td = soup("td")
    d1 = _find_current_stock_price(soup)
    d2 = _find_current_change_rate(soup)
    d3 = _find_Q4_sales(tags_td)
    d4 = _shares_owned_by_inst(tags_td)
    d5 = _dividend_yield(tags_td)
    data = dict(d1, **d2)
    data.update(d3)
    data.update(d4)
    data.update(d5)
#    data = dict(d1, d2, d3, d4, d5)
#    data['Current Stock price'] = _find_current_stock_price(soup)
#    data['Change rate'] = _find_current_change_rate(soup)
#    data['Q4 2018 sales'] = _find_Q4_sales(tags_td)
#    data['Shares owned by Institutional Holders'] = _shares_owned_by_inst(tags_td)
#    data['Dividend Yield'] = _dividend_yield(tags_td)
    return data

#%%
def _handle_request_result_and_build_soup(request_result):
  if request_result.status_code == 200:
    html_doc =  request_result.text
    soup = BeautifulSoup(html_doc,"html.parser")
    return soup
#%%
def _clean_string(string): # remove \t, \n, (, ), whitespace
    return re.sub('\s+|\\(|\\)',' ',string).strip() # Note : % is kept

    #%%
def _find_current_stock_price(soup):   
    d1 = {}
    # Searching stock price in soup
    tag_stock = soup.find_all("span", style=True)[0].text
    # tag_stock = soup.find_all('span')[5] # alternative searching way
    d1['Current Stock price']= _clean_string(tag_stock)
    return d1

#%%
def _find_current_change_rate(soup):    
    d2 ={}
    tag_stock_var = soup.find_all("span", class_= "valueContentPercent")[0]
    stock_var_raw = tag_stock_var.findAll('span')[0].contents[0].string
    d2['Change rate'] = _clean_string(stock_var_raw)  
    return d2
    
#%%
def _find_Q4_sales(tags_td):     # Find quarter sales (mean) at end 2018
    d3={}
    Q4_list = []
    for i in range(len(tags_td)):
        if tags_td[i].text == 'Quarter Ending\xa0Dec-18':
            Q4_list.append(tags_td[i+2].text)
    d3['Q4 2018 sales'] = Q4_list[0]
    return d3 # 2 values found (sales & earnings): only sales is kept
    # TODO: replace string with comma for thousand by a number 

#%%

def _shares_owned_by_inst(tags_td):
    d4 ={}
    for i in range(len(tags_td)):
        if tags_td[i].text == '% Shares Owned:':
            d4['Shares owned by Institutional Holders'] = tags_td[i+1].text
    return d4

#%%
    
def _dividend_yield(tags_td): # function with list
    d5 = {}
    yield_list = []
    for i in range(len(tags_td)):
        if tags_td[i].text == 'Dividend Yield':
            d5['Dividend Yield Company'] = tags_td[i+1].text
            d5['Dividend Yield Industry'] = tags_td[i+2].text
            d5['Dividend Yield Sector'] = tags_td[i+3].text
    return d5
        
#def _dividend_yield(tags_td): # Alternative with dict
#    yield_dict = {}
#    for i in range(len(tags_td)):
#        if tags_td[i].text == 'Dividend Yield':
#            yield_dict['Yield Company'] = tags_td[i+1].text
#            yield_dict['Yield Industry'] = tags_td[i+2].text
#            yield_dict['Yield Sector'] = tags_td[i+3].text
#    return yield_dict

#%%
companies = ['LVMH.PA', 'AIR.PA', 'DANO.PA']
result = get_key_figures(companies)
print(result)

#expected_result = 
#
#class Lesson2Tests(unittest.TestCase):
#    def testGetKeyFigures(self):
#        self.assertEqual(get_key_figures(companies), expected_result)
#        
#def main():
#    unittest.main()
#
#if __name__ == '__main__':
#    main()
    