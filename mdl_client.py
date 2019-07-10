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