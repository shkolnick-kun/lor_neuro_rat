#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import aiohttp
import asyncio

PROTO = 'http'
HOST = '127.0.0.1'
PORT = '9000'

URL_BASE = PROTO + '://' + HOST + ':' + PORT + '/api'

async def post_test(method, params, id):
    async with aiohttp.ClientSession() as session:
        par = {
            'jsonrpc':'2.0',
            'method':str(method),
            'params':params,
            'id':str(id)
        }
        async with session.post(URL_BASE, json=par) as response:
            res = await response.text()
            return res

TST_PARAMS = [
    {'id':'aaa', 'txt':'Мама мыла раму.'},
    {'id':'abc', 'txt':'Ждем ебилдов!'},
    {'id':'bcd', 'txt':'Ты идиот? Нет, ты - полный дебил!!'},
    {'id':'def', 'txt':'Ррря хррряя свниья порвалась!'}
]

async def main():
    res = await post_test('pass', TST_PARAMS, 'aaabbbcccddd')
    print(res)

    res = await post_test('classify', TST_PARAMS, '11122223333')
    print(res)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())