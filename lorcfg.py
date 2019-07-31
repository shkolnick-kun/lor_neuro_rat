#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 25 23:44:39 2019
@author: anon
"""
from keras.backend.tensorflow_backend import set_session
from tensorflow import ConfigProto
from tensorflow import Session

config = ConfigProto()
config.gpu_options.per_process_gpu_memory_fraction = 0.2
config.gpu_options.allow_growth = True
set_session(Session(config=config))

LOGIN  = 'user'
PASS = 'pass'
REPORT_TO = '15075051'
ONE_SHOT = False

OUT_FILE = 'log.txt'

#Parser base path
PARSER_BASE_PATH = 'data/download'

#Rat data path
BOT_BASE_PATH = 'data/work'

#LOR bin classifier:
BIN_TOKENIZER = 'models/tokenizer_bin_05072019.json'
BIN_CLASSIFIER = 'models/best_model_bin_05072019.h5'
BIN_THR = 0.8

#LOR cat classifier
CAT_TOKENIZER = 'models/tokenizer_cat_03072019.json'
CAT_CLASSIFIER = 'models/best_model_cat_03072019.h5'
CAT_LIST = 'models/cat_list_03072019.pkl'

MAX_LEN = 150
BATCH_SIZE = 8


