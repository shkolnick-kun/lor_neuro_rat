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
from json import JSONDecoder#, JSONEncoder
import os
import pickle as pk
import re
from time import sleep

#from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.models import load_model
import pandas as pd

from scrapy.spiders import Spider
from scrapy.http import Request, FormRequest

from clean_text import data_prepare

import lorcfg as cfg
###############################################################################
class LOR_classifier():
    def __init__(self, tokenizer_fname, model_fname, max_len, thr = 0.5, batch_size=512):
        with open(tokenizer_fname, 'rb') as f:
            self.tokenizer = pk.load(f)
        self.classifier = load_model(model_fname)
        self.maxlen = max_len
        self.batch_size = batch_size
        self.thr = thr
    
    def find_suspicious(self, X):
        print(X.head())
        X = data_prepare(X, verbous=False).copy()
        X_str = [' '.join(tokens) for tokens in list(X['Tokens'])]
        X_seq = self.tokenizer.texts_to_sequences(X_str)
        X_seq = pad_sequences(X_seq, maxlen=self.maxlen)
        y = self.classifier.predict(X_seq, verbose=0, batch_size=self.batch_size)
        return X[y > self.thr].copy()
###############################################################################
def merge_topic_versions(old, new):
    merge = pd.merge(old[['MsgId', 'Txt', 'Code', 'Quotes']], new, 
                     how = 'outer', 
                     on= 'MsgId', 
                     suffixes= ('_old', '_new'), 
                     indicator= False)

    idxs = merge["Txt_old"] != merge["Txt_new"]
    merge['Txt'] = merge['Txt_new'].where(idxs, merge['Txt_old'])
    update = idxs

    idxs = merge["Code_old"] != merge["Code_new"]
    merge['Code'] = merge['Code_new'].where(idxs, merge['Code_old'])
    update |= idxs

    idxs = merge["Quotes_old"] != merge["Quotes_new"]
    merge['Quotes'] = merge['Quotes_new'].where(idxs, merge['Quotes_old'])
    update |= idxs

    drop_list = ['Txt_old', 'Txt_new', 
                 'Code_old', 'Code_new', 
                 'Quotes_old', 'Quotes_new'] 
    merge.drop(drop_list, axis= 1, inplace= True)
    
    return merge, merge[update].copy()
###############################################################################
class LORTopic():
    def __init__(self, url, mod_time):
        self.url = url
        self.mod_time = mod_time
    
    def update(self, mod_time):
        if self.mod_time != mod_time:
            self.mod_time = mod_time
            return [self.url]
        return []
###############################################################################
class LORTracker():
    topic = []
    url = []
    
    def update(self, topic_url, mod_time):
        if topic_url not in self.url:
            self.url.append(topic_url)
            self.topic.append(LORTopic(topic_url, mod_time))
            return [topic_url]
        return self.topic[self.url.index(topic_url)].update(mod_time)
###############################################################################
class LORSpider(Spider):
    """
    TODO: Сделать скрипт более устойчивым к преждевременным остановкам

    1. Научиться обходит "автобаны" с помощью списков проксей.
    Списко проксей можно формировать отдельным скриптом.
    """
    name = 'GetLOR'
    domain_name = 'https://www.linux.org.ru'
    tracker_page = domain_name + '/tracker/'
    profile_page = domain_name + '/people/' + cfg.LOGIN + '/profile'
    start_urls = [domain_name + '/login.jsp']
    
    classifier = LOR_classifier(cfg.TOKENIZER, 
                                cfg.CLASSFIER, 
                                cfg.MAX_LEN, 
                                cfg.THR, 
                                cfg.BATCH_SIZE)
    suspicious = ''
    
    tracker = LORTracker()
    topic = []
    update = 10
    #==========================================================================
    def __init__(self, name=None, **kwargs):
        Spider.__init__(self, name, **kwargs)
    #==========================================================================
    def log_print(self, *_objects, _sep=' ', _end=' '):
        """
        Print to log, using print function and StringIO
        """
        pf = StringIO()
        print(*_objects, sep=_sep, end=_end, file=pf, flush=True)
        self.log(pf.getvalue())
        pf.close()
    #==========================================================================
    def parse(self, response):
        """
        Entry point of crawler FSM
        """
        self.log_print('Will logg in...')
        return self.do_login(response)
    #==========================================================================
    def on_login(self, response):
        jsd = JSONDecoder()
        res = jsd.decode(response.body_as_unicode())
        if res['username'] == cfg.LOGIN and res['loggedIn']:
            self.log_print('Logged in... Will do the job...')
            #Постим сообщение
            #return Request(self.domain_name + '/add_comment.jsp?topic=%s'%cfg.REPORT_TO, 
            #               callback=self.on_report_form_enter)
            self.topic = []
            return Request(self.tracker_page, callback=self.on_tracker_enter)
        return None
    #--------------------------------------------------------------------------
    def do_login(self, response):
        """
        Логика, отвечающая за логин
        """
        token = response.css('input[name="csrf"]::attr(value)').get()

        login_data = {
                'csrf': token,
                'nick': cfg.LOGIN,
                'passwd': cfg.PASS
                }
        return FormRequest.from_response(response,
                                         formdata=login_data,
                                         callback=self.on_login,
                                         dont_filter=True)
    #==========================================================================
    def go_next(self, response):
        #Обходим все страницы из self.topic
        if self.topic:    
            next_topic = self.topic[0]
            next_url = self.domain_name + next_topic
            self.log_print('Will goto:', next_url)
            sleep(4)
            return Request(next_url, 
                           callback=self.on_topic_enter, 
                           dont_filter=True)
        #Топики кончились, идем обратнов архив
        self.topic = []
        return Request(self.tracker_page, 
                       callback=self.on_tracker_enter,
                       dont_filter=True)
    #==========================================================================
    def on_tracker_enter(self, response):
        """
        Парсим страницы трекера, форомируем список URL-ов для топиков
        """
        self.log_print('==================================')
        #Список топиков на текущей странице трекера
        page_topic = []
        #Таблица с топиками/разделами
        msgtable = response.css('table[class="message-table"]').css('tbody')
        #Список разделов
        groups = msgtable.css('a[class="secondary"]::attr(href)').getall()
        for row in msgtable.css('tr'):
            topic_url = ''
            for l in row.css('a::attr(href)').getall():
                l = l.split('?')[0]
                if l not in groups:
                    url = l.split('/')
                    if 'page' in url[-1]:
                        url.remove(url[-1])
                    topic_url = '/'.join(url)
                        
            print(topic_url)
            mod_time = row.css('td[class="dateinterval"]').css('time::attr(datetime)').get()
            page_topic += self.tracker.update(topic_url, mod_time)
        #
        if page_topic:
            #Пополняеем список топиков
            self.topic += page_topic
            #Переходим к следующей странице трекера 
            for ref in response.css('div[class="nav"]').css('a[href*="?offset="]'):
                if 'следующие' in ref.css('::text').get():
                    sleep(2)
                    next_page = ref.css('::attr(href)').get()
                    self.log_print('Will goto:', next_page)
                    return Request(self.domain_name + next_page, 
                                   callback=self.on_tracker_enter,
                                   dont_filter=True)
#        if self.topic:
#            #Обходим топики
#            next_topic = self.topic[0]
#            next_url = self.domain_name + next_topic
#            self.log_print('Will goto:', next_url)
#            sleep(4)
#            return Request(next_url, 
#                           callback=self.on_topic_enter, 
#                           dont_filter=True)
                
        return self.go_next(response)
    #==========================================================================
    def on_report_form_enter(self, response):
        form = response.css('form[action="/add_comment.jsp"]')
        if form:
            self.log_print('+++++++++++++++++++++++++++++++++++')
            self.log_print(self.suspicious)
            self.log_print('+++++++++++++++++++++++++++++++++++')
            token = form.css('input[name="csrf"]::attr(value)').get()
            topic = form.css('input[name="topic"]::attr(value)').get()
            replyto = form.css('input[name="replyto"]::attr(value)').get()
            self.log_print(token,topic,replyto)
            data = {
                    'csrf': token,
                    'topic': topic,
                    'replyto': replyto,
                    'mode':'markdown',
                    'title':'Нейроябеда',
                    'msg':'Подозрительные сообщения:\n' + self.suspicious
                    }
            self.suspicious = ''
            return FormRequest.from_response(response,
                                         formdata=data,
                                         callback=self.go_next,
                                         dont_filter=True)
        self.log_print('Не удалось запостить!!!')
        return self.logout(response)
    #==========================================================================
    def get_comments(self, response):
        """
        Получение данных из комментариев
        """
        #jse = JSONEncoder()
        #posts = []
        msg_igs = []
        creators = []
        create_times = []
        mod_times = [] #Время модификации
        src_links = []
        del_reasons = []
        texts = []
        codes = []
        quotes = []
        #del_count = 0
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
                        #del_reason = l
                        #del_count += 1
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
        topic_new = self.get_comments(response)
        out_file = cfg.BOT_BASE_PATH + '/topic' + re.sub(r'/', '_', self.topic[0]) + '.pkl'
        #Обновление топика
        if os.path.isfile(out_file):
            topic_old = pd.read_pickle(out_file)
            topic_old.to_pickle(out_file + '.bak')
            topic_data, classify_data = merge_topic_versions(topic_old, topic_new)
        else:
            topic_data = topic_new
            classify_data = topic_new.copy()
        #
        topic_data.to_pickle(out_file)
        #Этот топик мы уже прошли
        self.topic.remove(response.url.split(self.domain_name)[1])
        #Находим подозрительные комментарии
        if len(classify_data) > 1:
            #TODO: Пока так, дальше посмотрим
            sel = classify_data['MsgId'].apply(lambda x: 'topic-' not in x)
            classify_data = classify_data[sel].copy()
            classify_data.reset_index(inplace=True, drop=True)
            sel = None

            cls_res = self.classifier.find_suspicious(classify_data)
            if len(cls_res) > 0:
                msg_ids = [mid.split('-')[1] for mid in cls_res['MsgId']]
                top_ids = list(cls_res['TopId'])
                #
                self.suspicious = ''
                for i, msg in enumerate(msg_ids):
                    url = top_ids[i] + '?cid=' + msg
                    self.suspicious += ' * ' + url   
                    #Постим сообщение
                    return Request(self.domain_name + '/add_comment.jsp?topic=%s'%cfg.REPORT_TO, 
                           callback=self.on_report_form_enter,
                           dont_filter=True)
        
        return self.go_next(response)
    #--------------------------------------------------------------------------
    def on_topic_enter(self, response):
        """
        Зашли в топик, жмем кнопку "Показать удаленные сообщения"
        """
        self.log_print('==================================')
        self.log_print('Topics left:', len(self.topic))
        self.log_print('==================================')
        form = response.css('form[action="%s"]'%self.topic[0])
        token = form.css('input[name="csrf"]::attr(value)').get()
        sleep(1)
        return FormRequest.from_response(response,
                                         formdata={'csrf': token, 'deleted':'1'},
                                         callback=self.get_topic_messages,
                                         dont_filter=True)
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
        Закончили сбор данных, выходим
        """
        print(response)
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
        Закончили сбор данных, собираемся выходить
        """
        self.log_print('Will logg out...')
        return Request(self.profile_page, callback=self.do_logout)
###############################################################################
if __name__ == '__main__':
    from scrapy.crawler import CrawlerProcess

    process = CrawlerProcess({
            'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'})

    process.crawl(LORSpider)
    process.start()
    process.join()
else:
    SPIDER = LORSpider()
