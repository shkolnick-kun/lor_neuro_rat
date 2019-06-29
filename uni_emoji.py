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
import re

lines = []

#TODO: Update emoji-test.txt from https://unicode.org/Public/emoji/
with open('emoji-test.txt', 'r', encoding='utf8') as data:
    lines = data.readlines()

emojis = []
for l in lines:
    #Drop comment strings
    if l[0] is '#':
        continue
    m = l.split('; ')
    if len(m)!=2:
        if __name__ == '__main__':
            print(l)
        continue
    cps, r = m
    #Form match string
    key = ''
    for codepoint in cps.split():
        key += chr(int(codepoint, 16))
    #Clean key    
    key = re.sub(r'\(', '\(', key)
    key = re.sub(r'\)', '\)', key)
    key = re.sub(r'\{', '\{', key)
    key = re.sub(r'\}', '\}', key)
    key = re.sub(r'\[', '\[', key)
    key = re.sub(r'\]', '\]', key)
    key = re.sub(r'\|', '\|', key)
    key = re.sub(r'\?', '\?', key)
    key = re.sub(r'\\', r'\\\\', key)
    key = re.sub(r'\.', '\.', key)
    key = re.sub(r'\*', '\*', key)
    key = re.sub(r'\+', '\+', key)
    key = re.sub(r'\^', '\^', key)    
    #Пробуем ускорить
    key = re.compile(key)
    #Get value
    #TODO: How about using only fully-qualified patterns???
    m = r.split('# ')
    if len(m)!=2:
        if __name__ == '__main__':
            print(l)
        continue
    _,value = m
    #Оставляем только расшифровку emoji
    value = re.sub(r'[^a-zA-Z ]+', '', value)
    
    emojis.append((key, value))

UNI_EMOJI = dict(emojis)

emojis = None
