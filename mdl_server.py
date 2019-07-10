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
from enum import Enum
import pickle as pk
import struct as st
#import sys
import traceback
#IO
import aiohttp
from aiohttp import web
import asyncio
import concurrent.futures
from functools import partial
#AI
import numpy as np
from keras.preprocessing.sequence import pad_sequences
from keras.models import load_model

from clean_text import text_preprocess
#------------------------------------------------------------------------------
#Пишу быстро. Минимум проверок на корректность.
#------------------------------------------------------------------------------
#Конфигурация пока будет здесь (можно сделать опции запуска)
#import multiprocessing
#multiprocessing.set_start_method('spawn', True)

from keras.backend.tensorflow_backend import set_session
from tensorflow import ConfigProto
from tensorflow import Session
from tensorflow import global_variables_initializer
from tensorflow import get_default_graph

config = ConfigProto()
config.gpu_options.per_process_gpu_memory_fraction = 0.2
config.gpu_options.allow_growth = True

sess = Session(config=config)
sess.run(global_variables_initializer())

def config_start():
    default_graph = get_default_graph()
    default_graph.finalize()
    return default_graph

#Где поднимаем сервер
MDL_SEVER_HOST = '127.0.0.1'
MDL_SEVER_PORT = 9000
#LOR bin classifier:
MDL_BIN_TOK = 'models/tokenizer_bin_05072019.pkl'
MDL_BIN_CLS = 'models/best_model_bin_05072019.h5'
MDL_BIN_THR = 0.8
#LOR cat classifier
MDL_CAT_TOK = 'models/tokenizer_cat_03072019.pkl'
MDL_CAT_CLS = 'models/best_model_cat_03072019.h5'
MDL_CAT_LST = 'models/cat_list_03072019.pkl'

MDL_MAX_LEN = 150
MDL_BATCH_SIZE = 8
#------------------------------------------------------------------------------
class RpcErr(Enum):
    EPARSE = {'code':-32700, 'message':'Parse error'}
    EINRQ = {'code':-32600, 'message':'Invalid Request'}
    EMETH = {'code':-32601, 'message':'Method not found'}
    EINPAR = {'code':-32602, 'message':'Invalid params'}
    EERROR = {'code':-32603, 'message':'Internal error'}
#------------------------------------------------------------------------------
def server_error(code=-32000, msg='Server error'):
    if code < -32099:
        print('Warning: error code: %d is out of bounds!')
        code = -32099
    return {'code':code, 'message':str(msg)}
#------------------------------------------------------------------------------
def _jrpc_error(err, rq_id):
    #
    print('Err type: ', type(err))
    if type(err) is RpcErr:
        err = err.value
    #
    resp_data = {
        'jsonrpc':'2.0',
        'error':err,
        'id':str(rq_id)
    }
    print('Response: ', resp_data)
    return web.json_response(resp_data)
#------------------------------------------------------------------------------
#Пока так...
class TxtModel():
    """
    Обертка над моделью keras
    """
    def __init__(self, tokenizer_fname, model_fname):
        """
        tokenizer_fname - имя файла токенизатора
        model_fname - имя файла модели
        """
        #Токенизатор
        with open(tokenizer_fname, 'rb') as f:
            self.tok = pk.load(f)
        #Модель
        self.mdl = load_model(model_fname)
        self.mdl._make_predict_function()
    #--------------------------------------------------------------------------
    def predict(self, X):
        """
        X - список с тектов
        Возвращает результаты работы модели с текстами из X
        """
        tok = [text_preprocess(s)[1] for s in X]
        X_str = [' '.join(tokens) for tokens in tok]
        X_seq = self.tok.texts_to_sequences(X_str)
        X_seq = pad_sequences(X_seq, maxlen=MDL_MAX_LEN)
        return self.mdl.predict(X_seq, verbose=0, batch_size=MDL_BATCH_SIZE)
#------------------------------------------------------------------------------
mdl_bin_cls = None
mdl_cat_cls = None
mdl_cat_lst = None
#------------------------------------------------------------------------------
from time import sleep
def _do_classify(data):
    global mdl_bin_cls
    global mdl_cat_cls
    global mdl_cat_lst
    txt_id = []
    text = []
    for rec in data:
        txt_id.append(rec['id'])
        text.append(rec['txt'])
    pos_index = [-1]*len(text)
    #Бинарная классификация
    print(text)
    bin_res = mdl_bin_cls.predict(text)
    pos_text = []
    for i, br in enumerate(bin_res):
        if br > MDL_BIN_THR:
            pos_text.append(text[i])
            pos_index[i] = len(pos_text) - 1
    #Категориальная классификация
    cat_res = mdl_cat_cls.predict(pos_text)
    #Формируем результат
    res = []
    for i, pi in enumerate(pos_index):
        if pi >= 0:
            cp = dict(zip(mdl_cat_lst, [float(c) for c in cat_res[pi]]))
            res.append({'id':txt_id[i], 'bin_prob': float(br[0]), 'cat_prob':cp})
        else:
            res.append({'id':txt_id[i], 'bin_prob': float(br[0])})
    return res
#------------------------------------------------------------------------------
def _do_classify_wrapper(data):
    try:
        return None, _do_classify(data)
    except:
        return server_error(msg = traceback.format_exc()), []
#------------------------------------------------------------------------------
executor = None
loop = None
async def _classify_data(data):
    global executor
    global loop
    return await loop.run_in_executor(executor, partial(_do_classify_wrapper, data))
#------------------------------------------------------------------------------
METHOD_DISPATCH = {
    'classify':_classify_data
}
#------------------------------------------------------------------------------
METHODS = list(METHOD_DISPATCH)
#------------------------------------------------------------------------------
async def do_work(request):
    if not request.body_exists:
        return _jrpc_error(RpcErr.EINRQ, 0)
    print('Will parse the request...')
    #
    try:
        rq = await request.json()
        print('Got json...')
        #
        if rq['jsonrpc'] != '2.0':
            return _jrpc_error(RpcErr.EINRQ, rq['id'])
        print('JSON RPC 2.0...')
        #
        if rq['method'] not in METHODS:
            return _jrpc_error(RpcErr.EMETH, rq['id'])
        #
        print('Method: ', str(rq['method']))
        err, res = await METHOD_DISPATCH[rq['method']](rq['params'])
        #
        if err:
            print('Error: ', err)
            return _jrpc_error(err, rq['id'])
        #
        resp_data = {
            'jsonrpc':'2.0',
            'result':res,
            'id':str(rq['id'])
        }
        print('Success: ', resp_data)
        return web.json_response(resp_data)
    except:
        traceback.print_exc()
        return _jrpc_error(RpcErr.EPARSE, 0)
#------------------------------------------------------------------------------
async def gateway_factory():
    global mdl_bin_cls
    global mdl_cat_cls
    global mdl_cat_lst
    #
    global executor
    global loop
    #
    mdl_bin_cls = TxtModel(MDL_BIN_TOK, MDL_BIN_CLS)
    mdl_cat_cls = TxtModel(MDL_CAT_TOK, MDL_CAT_CLS)
    #
    loop = asyncio.get_event_loop()
    #Для работы tf с multiporcessing нужна "магия", пока не осилил.
    # Как вариант, можно определить все, что связано с моделями в отдельном
    # модуле и импортировать его уже в форкнутом процессе. 
    #
    # Тогда вся рабта с моделями будет происходить в одном единственном процессе, 
    # и "магия" не понядобится, понадибится только перенаправить 
    # sdtout и sdterr в Pipe/Queue, ну и RPC тоже сделать через Pipe/Queue.
    #
    # В этом случае на асинхронной стороне можно будет сделать связь 
    # с помощью ThreadPoolExecutor и этих самых Pipe/Queue
    #executor = concurrent.futures.ProcessPoolExecutor(max_workers=1)
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    #
    with open(MDL_CAT_LST, 'rb') as f:
        mdl_cat_lst = pk.load(f)
    #
    app = web.Application()
    app.add_routes([web.post('/api', do_work)])
    return app
#------------------------------------------------------------------------------
if __name__ == '__main__':
    web.run_app(gateway_factory(), host=MDL_SEVER_HOST, port=MDL_SEVER_PORT)
