#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan  5 21:05:54 2019

@author: anon
"""
import gensim
from pymagnitude import *
import time

heli = ['вертолет']

multi = ['мама','папа','ребенок','соль','фасоль','компьютер','спутник','цапля','щенок','разделывать']

#mg = Magnitude('/tmp/wiki.ru.magnitude')
s = time.time()
mg = Magnitude('Vectors/araneum_none_fasttextskipgram_300_5_2018/araneum_none_fasttextskipgram_300_5_2018.magnitude')
print("Magnitude load time:",time.time() - s)

def query_mg(words):
    s = time.time()
    #ret = [mg.query(str(w)) for w in words]
    ret = mg.query(words)
    print('Magnitude query time:',time.time() - s)
    return ret
#Холодно
m = query_mg(heli)
#Тепло
n = query_mg(heli)
#Холодно
k = query_mg(multi)
#Тепло
l = query_mg(multi)

#a = mg.query('колумбайн')# - mg.query('мужчина') + mg.query('женщина')
#print(mg.most_similar(a, topn=5))


s = time.time()
ft = gensim.models.fasttext.FastText.load('Vectors/araneum_none_fasttextskipgram_300_5_2018/araneum_none_fasttextskipgram_300_5_2018.model')
print("FastText load time:",time.time() - s)

def query_ft(words):
    s = time.time()
    #ret = [ft.wv[str(w)] for w in words]
    ret = ft.wv[words]
    print('FastText query time:',time.time() - s)
    return ret

#Холодно
m = query_ft(heli)
#Тепло
n = query_ft(heli)
#Холодно
k = query_ft(multi)
#Тепло
l = query_ft(multi)

