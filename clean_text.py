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

#import numpy as np
#import math
from nltk.corpus import stopwords
#from nltk import word_tokenize

import pandas as pd
from progressbar.bar import ProgressBar
#from pymystem3 import Mystem
import pymorphy2
import re

#from transliterate import translit

from uni_emoji import UNI_EMOJI
from emoji import EMOJI
from jafa import JAFA

def voc_relace(r, voc):
    for e in list(voc):
        r = re.sub(e, ' ' + voc[e] + ' ', r)
    return r

# word from num
WFN = {r'0': 'ноль',
       r'1': 'один',
       r'2': 'два',
       r'3': 'три',
       r'4': 'четыре',
       r'5': 'пять',
       r'6': 'шесть',
       r'7': 'семь',
       r'8': 'восемь',
       r'9': 'девять'}

#WFN = {r'0-9': ''}
URL_PAT = re.compile(r'(?i)(?:(https?|s?ftp):\/\/)?(?:www\d{0,3}\.)?((?:(?:[\w][\w-]{0,61}[\w]\.)+)([\w]{2,6})|(?:\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}))(?::(\d{1,5}))?(?:(\/\S+)*)')
HASH_PAT = re.compile(r'\#')
LB_PAT = re.compile(r'\(')
RB_PAT = re.compile(r'\)')
ID_PAT = re.compile(r'\[id[0-9]+\|.+\]')
CLUB_PAT = re.compile(r'\[club[0-9]+\|.+\]')
RU_EN_DIG_PAT = re.compile(r'[^a-zA-Zа-яА-ЯёЁ0-9\n\r]+')

def text_clean(r):
    # URL
    #(?i)(?:(https?|s?ftp):\/\/)?(?:www\d{0,3}\.)?((?:(?:[\w][\w-]{0,61}[\w]\.)+)([\w]{2,6})|(?:\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}))(?::(\d{1,5}))?(?:(\/\S+)*)
    #r = re.sub(r'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))', 'ссылка ', r)
    
    r = re.sub(URL_PAT, 'ссылка ', r)
    # Символы юникода, emoji
    r = voc_relace(r, UNI_EMOJI)
    # хештеги
    r = re.sub(HASH_PAT, 'хеш ', r) #Заменять на пробел?
    # Смайлики
    r = voc_relace(r, EMOJI)
    # Считаем скобки смайлики
    s_pos = len(re.findall(RB_PAT, r))
    s_neg = len(re.findall(LB_PAT, r))
    if s_pos != s_neg:
        if s_pos > s_neg:
            r = 'веселый ' + r
        else:
            r = 'печальный ' + r
    # Замена айдишников, чтоб не оверфитить на них
    r = re.sub(ID_PAT, ' ', r) #Заменять на пробел?
    r = re.sub(CLUB_PAT, ' ', r) #Заменять на пробел?
    # Оставляем только русские и английские буквы и цифры
    r = re.sub(RU_EN_DIG_PAT, ' ', r)
    # Замена сокращений
    r = voc_relace(r, JAFA)
    # Замена цифр на их обозначения
    r = voc_relace(r, WFN)
    #Убираем множественные пробелы
    r = re.sub(r' +', ' ', r)
    #Пробелы вначале строки
    r = re.sub(r'\n ', '\n', r)
    #Транслит
    #r = translit(r, 'ru')
    return r
#=============================================================================
print('Стоп-слова:')
try:
    print(stopwords.words('russian'))
except Exception:
    import nltk
    nltk.download('stopwords')
    print(stopwords.words('russian'))

NUMS = [WFN[r] for r in list(WFN)]
stop_words = [w for w in stopwords.words('russian') if w not in NUMS]

PLS = ['я','ты','oн','oна','его','вы','ее','её','мне','меня','ему','него','oн',
       'вас','ваш','вам','себя','ей','oни','ней','мы','тебя','себе','этот',
       'того','этого','ним','этом','мой','нее','неё','тот','эту','моя','свою',
       'этой','том','им']
stop_words = [w for w in stop_words if w not in PLS]

morph = pymorphy2.MorphAnalyzer()
def text_preprocess(s):
    global stop_words
    s = text_clean(str(s))
    words = s.lower().split()
    tokens = []
    for w in words:
        w = voc_relace(w, JAFA)
        p = morph.parse(w)[0]
        tokens.append(p.normal_form)
    #Теперь можно удалить стоп-слова
    tokens = [t for t in tokens if not t in stop_words]
    words  = [w for w in words if not w in stop_words]
    return words, tokens
#=============================================================================
def data_prepare(x, verbous=True):
    X = x.copy()
    #Пока так
    if verbous:
        print('Склеиваем строки...')
    X['Text'] = X['Txt'].apply(lambda x: ' '.join(x)) 
    if verbous:
        print('Готово\nНормализиция текстов...')

    X['Words'] = pd.Series([[]]*len(X))
    X['WrdCnt'] = pd.Series([0]*len(X))
    X['Tokens'] = pd.Series([[]]*len(X))
    X['TokCnt'] = pd.Series([0]*len(X))
    
    if verbous:
        pb = ProgressBar(max_value = len(X))
        pb.start()
        
    for i in range(0,len(X)):
        if verbous:
            pb.update(i)
        w,t = text_preprocess(X.loc[i,'Text'])
        X.at[i,'Words'] = w
        X.at[i,'WrdCnt'] = len(w)
        X.at[i,'Tokens'] = t
        X.at[i,'TokCnt'] = len(t)
    if verbous:
        pb.finish()
    
    if verbous: 
        X['TokCnt'].hist(bins=100)
        X['WrdCnt'].hist(bins=100)
    return X
#=============================================================================
if __name__ == '__main__':
    X = pd.read_pickle('data/Dataset1с.pkl')
    X = data_prepare(X)
    X.to_pickle('data/XyWrdTok1с.pkl')
    print(X.describe())
    X = pd.read_pickle('data/Dataset2с.pkl')
    X = data_prepare(X)
    X.to_pickle('data/XyWrdTok2с.pkl')
    print(X.describe())
    X = pd.read_pickle('data/Dataset5с.pkl')
    X = data_prepare(X)
    X.to_pickle('data/XyWrdTok5с.pkl')
    print(X.describe())
    X = pd.read_pickle('data/Dataset10с.pkl')
    X = data_prepare(X)
    X.to_pickle('data/XyWrdTok10с.pkl')
    print(X.describe())
