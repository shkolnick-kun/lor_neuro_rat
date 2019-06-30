#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 25 23:44:39 2019
@author: anon
"""

LOGIN  = 'user'
PASS = 'pass'
REPORT_TO = '15041564'
ONE_SHOT = False

OUT_FILE = 'log.txt'

#Rat data path
BOT_BASE_PATH = 'data/work'

#LOR bin classifier:
BIN_TOKENIZER = 'models/lor_tokenizer_с.pkl'
BIN_CLASSIFIER = 'models/lor_bin_class_c.h5'
BIN_THR = 0.8
#LOR cat classifier
CAT_TOKENIZER = 'models/tokenizer_cat.pkl'
CAT_CLASSIFIER = 'models/cat_model.h5'
CAT_LIST = 'models/cat_list.pkl'

MAX_LEN = 150
BATCH_SIZE = 8
