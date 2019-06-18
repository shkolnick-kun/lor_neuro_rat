#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun  1 10:34:59 2019

@author: anon
"""
tree = []
with open('lor_tree.txt', 'r') as f:
    for br in f.readlines():
        tree.append(br[:-1])
tree.sort()
years = [2019]
months = [1,2,3,4,5]

arch_urls = []
for br in tree:
    for y in years:
        for m in months:
            arch_urls.append(br+str(y)+'/'+str(m)+'/\n')
            
with open('arch_urls.txt', 'w+') as f:
    f.writelines(arch_urls)