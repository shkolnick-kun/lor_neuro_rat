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
import os
import numpy as np
import pandas as pd
from progressbar.bar import ProgressBar

topics = []

drl = os.listdir('data/download')
drl.remove('arch.pkl')
drl.remove('topic.pkl')
drl.remove('topic_num.pkl')
pb = ProgressBar(max_value = len(drl))
pb.start()

for i, name in enumerate(drl):
    bname, ext = name.split('.')
    if 'topic_' in bname:
        topics.append(pd.read_pickle('data/download/'+name))
    pb.update(i)
pb.finish()

topic_data = pd.concat(topics, ignore_index=True, copy=True, sort=False)

N = len(topic_data)
deleted = len(topic_data[topic_data['DelReason'] != ''])
code = np.sum(np.array([len(code) for code in topic_data['Code']]))
quotes = np.sum(np.array([len(code) for code in topic_data['Quotes']]))

print(N, deleted, code, quotes)

topic_data.to_pickle('data/LOR_Txt_DataFrame.pkl')
        
