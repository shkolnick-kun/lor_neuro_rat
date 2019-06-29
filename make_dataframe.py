#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun  1 23:09:01 2019

@author: anon
"""

#import os
import pandas as pd
import pickle as pk
from progressbar.bar import ProgressBar

data = []
with open('data/all_data.pkl', 'rb') as f:
    tid, data = pk.load(f)
    
if not data:
    exit(-1)
    
msg_ids = []
creators = []
timestamps = []
src_links = []
del_reasons = []
texts = []
codes = []
quotes = []

pb = ProgressBar(max_value = len(data))
pb.start()
for i, rec in enumerate(data):
    msg_ids.append(rec['MsgId'])
    creators.append(rec['Creator'])
    timestamps.append(rec['Time'])
    src_links.append(rec['SrcLink'])
    del_reasons.append(rec['DelReason'])
    texts.append(rec['Txt'])
    codes.append(rec['Code'])
    quotes.append(rec['Quotes'])
    pb.update(i)
pb.finish()

data = None

print('Создаю DataFrame...')
df = pd.DataFrame({'TopId':tid,
                   'MsgId':msg_ids,
                   'Creator':creators,
                   'Time':timestamps,
                   'SrcLink':src_links,
                   'DelReason':del_reasons,
                   'Txt':texts,
                   'Code':codes,
                   'Quotes':quotes})

print('Сохраняю DataFrame...')
df.to_pickle('data/all_data_as_dataframe.pkl')
