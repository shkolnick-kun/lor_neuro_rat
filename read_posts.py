#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    This file is a part of the lor_neuro_rat project.
    Copyright (C) 2019 anonimous

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Please contact with me by E-mail: shkolnick.kun@gmail.com
"""
from json import JSONDecoder
import os
import pickle as pk
#import pandas as pd
import re
from progressbar.bar import ProgressBar

#from lorcfg import *

jsd = JSONDecoder()
rec = []
tid = []
deleted = 0
code = 0
quotes = 0
N = 0

drl = os.listdir('data/download')
pb = ProgressBar(max_value = len(drl))
pb.start()
for i, name in enumerate(drl):
    bname, ext = name.split('.')
    if 'txt' == ext:
        with open('data/download/'+name, 'r') as f:
            for l in f.readlines():
                N += 1
                rec.append(jsd.decode(l))
                tpath = re.sub(r'_', '/', bname)
                tpath = re.sub(r'thread', '', tpath)
                tid.append(tpath)
                
                if rec[-1]['DelReason']:
                    deleted += 1
                
                if rec[-1]['Code']:
                    code += 1
                    
#                if rec[-1]['Quotes']:
#                    quotes += 1
#                    print('=======================================')
#                    print(rec[-1]['Txt'])
#                    print(rec[-1]['Quotes'])
                pb.update(i)
pb.finish()
                
print(N, deleted, code, quotes)
        
with open('data/all_data.pkl', 'wb+') as f:
    pk.dump((tid, rec), f)