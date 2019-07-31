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
from io import StringIO
import json
from time import sleep

import pandas as pd

from scrapy.spiders import Spider
from scrapy.http import Request, FormRequest

import lorcfg as cfg
###############################################################################
class LORSpiderBase(Spider):
    """
    Базовый класс для парсеров LOR
    """
    domain_name = 'https://www.linux.org.ru'
    profile_page = domain_name + '/people/' + cfg.LOGIN + '/profile'
    start_urls = [domain_name + '/login.jsp']
    #==========================================================================
    def __init__(self, name=None, **kwargs):
        Spider.__init__(self, name, **kwargs)
    #==========================================================================
    def log_print(self, *_objects, _sep=' ', _end=' '):
        """
        Печать в лог с помощью print и StringIO
        """
        pf = StringIO()
        print(*_objects, sep=_sep, end=_end, file=pf, flush=True)
        self.log(pf.getvalue())
        pf.close()
    #==========================================================================
    def parse(self, response):
        """
        Точка входа в конечный автомат
        """
        self.log_print('Will logg in...')
        return self.do_login(response)
    #==========================================================================
    def has_logged_in(self, response):
        """
        Проверка удачночти логина
        """
        jsd = json.JSONDecoder()
        res = jsd.decode(response.body_as_unicode())
        if res['username'] == cfg.LOGIN and res['loggedIn']:
            self.log_print('Logged in... Will do the job...')
            return True
        return False
    #--------------------------------------------------------------------------
    def on_login(self, response):
        raise NotImplementedError("on_login must be implemented by spider!")
    #--------------------------------------------------------------------------
    def do_login(self, response):
        """
        Логика, отвечающая за логин
        """
        token = response.css('input[name="csrf"]::attr(value)').get()
        login_data = {'csrf': token,
                      'nick': cfg.LOGIN,
                      'passwd': cfg.PASS}
        return FormRequest.from_response(response,
                                         formdata=login_data,
                                         callback=self.on_login,
                                         dont_filter=True)
    #==========================================================================
    def go_next(self, response):
        """
        Логика переходов между состояниями
        """
        raise NotImplementedError("go_next must be implemented by spider!")
    #==========================================================================
    def get_comments(self, response):
        """
        Получение данных из комментариев
        """
        msg_igs = []
        creators = []
        create_times = []
        mod_times = [] #Время модификации
        src_links = []
        del_reasons = []
        texts = []
        codes = []
        quotes = []
        #
        s = response.css('article[class="msg"]')
        for sel in s:
            self.log_print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
            #Получение id сообщения
            msg_id = sel.css('::attr(id)').get()
            self.log_print(msg_id)
            #У комментариев и удаленных топиков есть title
            title = sel.css('div[class="title"]')
            title_txt = title.css('::text').getall()
            src_lnk = None
            del_reason = None
            for l in title_txt:
                #Извлечение сылки на исходный пост
                if not src_lnk:
                    if 'Ответ на' in l:
                        src_lnk = title.css('a[data-samepage="samePage"]::attr(href)').get()
                        self.log_print(src_lnk)
                #Извлечение причины удаления
                if not del_reason:
                    if 'Сообщение удалено' in l:
                        del_reason = l
                        self.log_print(del_reason)
            #
            blacklist = ['\n']
            #
            if 'comment' in msg_id:
                #Комментарий
                #Извлечение сообщения
                msg = sel.css('div[class="msg_body message-w-userpic"]')
                #Извлечение автора
                sign = msg.css('div[class="sign"]')
                creator = sign.css('a[itemprop="creator"]::attr(href)').get()
                #Извлечение времени
                ctime = sign.css('time[itemprop="commentTime"]::attr(datetime)').get()
                #Извлечение текстов
                txt_lines = msg.css('::text').getall()
                #Тут нет отдельного футтера
                blacklist += sign.css('::text').getall()
                blacklist += sel.css('div[class="reply"]').css('::text').getall()
            else:
                #Топик
                #Извлечение автора
                sign = sel.css('div[class="sign"]')
                creator = sign.css('a[itemprop="creator"]::attr(href)').get()
                #Извлечение времени
                ctime = sign.css('time[itemprop="dateCreated"]::attr(datetime)').get()
                #Извлечение текстов
                txt_lines = sel.css('div[itemprop="articleBody"]').css('::text').getall()
            #Выделяем код
            code = sel.css('div[class*="code"]').css('::text').getall()
            #Убираем код из текстов
            blacklist += code
            #Выделяем цитаты
            quote_lines = sel.css('blockquote').css('::text').getall()
            quote = [l for l in quote_lines if l not in blacklist and l.strip()]
            #Запоминаем цитаты с ответами + оригинальный текст
            txt = [l for l in txt_lines if l not in blacklist and l.strip()]
            #Ананим, лигион!!!
            if not creator:
                creator = ''
            #Оригинальное сообщение
            if not src_lnk:
                src_lnk = ''
            #Не удалено
            if not del_reason:
                del_reason = ''
            #Печатаем вытащенное
            self.log_print(creator)
            self.log_print(ctime)
            self.log_print(txt)
            self.log_print(code)
            self.log_print(quotes)
            #Будем делать pandas DataFrame
            msg_igs.append(msg_id)
            creators.append(creator)
            create_times.append(ctime)
            mod_times.append(ctime)#TODO: Сделать извлечение времен модификации
            src_links.append(src_lnk)
            del_reasons.append(del_reason)
            texts.append(txt)
            codes.append(code)
            quotes.append(quote)
        #Делаем DataFrame
        return pd.DataFrame({'TopId':[response.url]*len(msg_igs),
                             'MsgId':msg_igs,
                             'Creator':creators,
                             'Time':create_times,
                             'ModTime':mod_times,
                             'SrcLink':src_links,
                             'DelReason':del_reasons,
                             'Txt':texts,
                             'Code':codes,
                             'Quotes':quotes})
    #--------------------------------------------------------------------------
    def get_topic_messages(self, response):
        """
        Парсим топик, сохраняем сообщения
        """
        raise NotImplementedError("get_topic_messages must be implemented by spider!")
    #--------------------------------------------------------------------------
    def on_topic_enter(self, response):
        """
        Парсим топик, сохраняем сообщения
        """
        raise NotImplementedError("on_topic_enter must be implemented by spider!")
    #--------------------------------------------------------------------------
    def topic_enter_handler(self, response, urls):
        """
        Зашли в топик, жмем кнопку "Показать удаленные сообщения"
        """
        self.log_print('==================================')
        self.log_print('Topics left:', len(urls))
        self.log_print('==================================')
        form = response.css('form[action="%s"]'%urls[0])
        token = form.css('input[name="csrf"]::attr(value)').get()
        sleep(4)
        if form and token:
            return FormRequest.from_response(response,
                                             formdata={'csrf': token, 'deleted':'1'},
                                             callback=self.get_topic_messages,
                                             dont_filter=True)

        #Тема перемещена в архив, идем к следующей...
        return self.go_next(response)
    #==========================================================================
    def on_logout(self, response):
        """
        Выход произошел
        """
        self.log_print('Done!')
        return None
    #--------------------------------------------------------------------------
    def do_logout(self, response):
        """
        Закончили работу, выходим
        """
        self.log_print(response)
        self.log_print('Logging out...')
        form = response.css('form[action="logout"]')
        token = form.css('input[name="csrf"]::attr(value)').get()
        return FormRequest.from_response(response,
                                         formdata={'csrf': token},
                                         callback=self.on_logout,
                                         dont_filter=True)
    #--------------------------------------------------------------------------
    def logout(self, response):
        """
        Закончили работу, собираемся выходить
        """
        self.log_print('Will logg out...')
        return Request(self.profile_page, callback=self.do_logout)
