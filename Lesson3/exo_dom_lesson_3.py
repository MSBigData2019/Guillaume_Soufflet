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

#%%
# Retrieve soup from Github
url = 'https://gist.github.com/paulmillr/2657075'
res = requests.get(url)
if res.status_code == 200:
    html_doc =  res.text
    soup = BeautifulSoup(html_doc,"html.parser")

tds = soup("td")
#%%
# Retrieve urls of most active contributors
git_urls = []

for td in tds:
    try:
       if 'https://github.com/' in td.find("a").attrs['href']:
           git_urls.append(td.find("a").attrs['href'])             
    except:
        continue

git_urls = git_urls[0:256]

