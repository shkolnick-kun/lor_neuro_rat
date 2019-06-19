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
import pickle as pk
#import re
from time import sleep

from scrapy.spiders import Spider
from scrapy.http import Request, FormRequest

import lorcfg as cfg

DATA_BASE_PATH = 'data'
###############################################################################
class LORMessage():
    def __init__(self, msg_id, mod_time, text):
        self.msg_id = msg_id
        self.mod_time = mod_time
        self.text = text
        
    def update(self, mod_time, text):
        if self.mod_time != mod_time:
            self.text = text
            return text
        return []
###############################################################################
class LORTopic():
    def __init__(self, url, mod_time):
        self.url = url
        self.mod_time = mod_time
        self.msg = []
        self.msg_id = []
        
    def update(self, message):
        if message.msg_id not in self.msg_id:
            self.msg_id.append(message.msg_id)
            self.msg.append(message)
            return message.text
        return self.msg[self.msg_id.index(message.msg_id)].update(message.mod_time, message.text)
    
    def refresh(self, mod_time):
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
        return self.topic[self.url.index(topic_url)].refresh(mod_time)
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
    def on_report_form_enter(self, response):
        form = response.css('form[action="/add_comment.jsp"]')
        if form:
            token = form.css('input[name="csrf"]::attr(value)').get()
            topic = form.css('input[name="topic"]::attr(value)').get()
            replyto = form.css('input[name="replyto"]::attr(value)').get()
            self.log_print(token,topic,replyto)
            data = {
                    'csrf': token,
                    'topic': topic,
                    'replyto': replyto,
                    'mode':'markdown',
                    'title':'Тестовое сообщение',
                    'msg':'Бот зашел в топик и оставил это сообщение...'
                    }
            return FormRequest.from_response(response,
                                         formdata=data,
                                         callback=self.logout,
                                         dont_filter=True)
        self.log_print('Не удалось запостить!!!')
        return self.logout(response)
    #==========================================================================
    def on_tracker_enter(self, response):
        """
        Парсим страницы трекера, форомируем список URL-ов для топиков
        """
        self.log_print('==================================')
        msgtable = response.css('table[class="message-table"]').css('tbody')
        #Список разделов
        groups = msgtable.css('a[class="secondary"]::attr(href)').getall()
        for row in msgtable.css('tr'):
            topic_url = ''
            for l in row.css('a::attr(href)').getall():
                #
                l = l.split('?')[0]
                #
                if l not in groups:
                    topic_url = l
            #
            mod_time = row.css('td[class="dateinterval"]').css('time::attr(datetime)').get()
            self.topic += self.tracker.update(topic_url, mod_time)

        #for t in self.tracker.topic:
        #    print(t.url)            
    
        for ref in response.css('div[class="nav"]').css('a[href*="?offset="]'):
            if 'следующие' in ref.css('::text').get():
                sleep(2)
                next_page = ref.css('::attr(href)').get()
                self.log_print('Will goto:', next_page)
                return Request(self.domain_name + next_page, 
                               callback=self.on_tracker_enter,
                               dont_filter=True)
        #Пока просто печатаем топики
        print(self.topic)
        self.topic = []
        #Пока так
        if self.update > 0:
            self.update -= 1
            return Request(self.tracker_page, 
                           callback=self.on_tracker_enter, 
                           dont_filter=True)
            
        return self.logout(response)
        #Теперь обходим топики
        #self.log_print('Will visit topics...')
        #next_url = self.domain_name + self.topic.get()
        #return Request(next_url, callback=self.on_topic_enter)
#    #==========================================================================
#    def get_comments(self, response, out_file):
#        """
#        Получение данных из комментариев
#        """
#        jse = JSONEncoder()
#        posts = []
#        del_count = 0
#        s = response.css('article[class="msg"]')
#        for sel in s:
#            self.log_print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
#            #Получение id сообщения
#            msg_id = sel.css('::attr(id)').get()
#            self.log_print(msg_id)
#            #У комментариев и удаленных топиков есть title
#            title = sel.css('div[class="title"]')
#            title_txt = title.css('::text').getall()
#            src_lnk = None
#            del_reason = None
#            for l in title_txt:
#                #Извлечение сылки на исходный пост
#                if not src_lnk:
#                    if 'Ответ на' in l:
#                        src_lnk = title.css('a[data-samepage="samePage"]::attr(href)').get()
#                        self.log_print(src_lnk)
#                #Извлечение причины удаления
#                if not del_reason:
#                    if 'Сообщение удалено' in l:
#                        del_reason = l
#                        del_count += 1
#                        self.log_print(del_reason)
#            #
#            blacklist = ['\n']
#            #
#            if 'comment' in msg_id:
#                #Комментарий
#                #Извлечение сообщения
#                msg = sel.css('div[class="msg_body message-w-userpic"]')
#                #Извлечение автора
#                sign = msg.css('div[class="sign"]')
#                creator = sign.css('a[itemprop="creator"]::attr(href)').get()
#                #Извлечение времени
#                ctime = sign.css('time[itemprop="commentTime"]::attr(datetime)').get()
#                #Извлечение текстов
#                txt_lines = msg.css('::text').getall()
#                #Тут нет отдельного футтера
#                blacklist += sign.css('::text').getall()
#                blacklist += sel.css('div[class="reply"]').css('::text').getall()
#            else:
#                #Топик
#                #Извлечение автора
#                sign = sel.css('div[class="sign"]')
#                creator = sign.css('a[itemprop="creator"]::attr(href)').get()
#                #Извлечение времени
#                ctime = sign.css('time[itemprop="dateCreated"]::attr(datetime)').get()
#                #Извлечение текстов
#                txt_lines = sel.css('div[itemprop="articleBody"]').css('::text').getall()
#            #Выделяем код
#            code = sel.css('div[class*="code"]').css('::text').getall()
#            #Убираем код из текстов
#            blacklist += code
#            #Выделяем цитаты
#            quote_lines = sel.css('blockquote').css('::text').getall()
#            quotes = [l for l in quote_lines if l not in blacklist and l.strip()]
#            #Запоминаем цитаты с ответами + оригинальный текст
#            txt = [l for l in txt_lines if l not in blacklist and l.strip()]
#            #Ананим, лигион!!!
#            if not creator:
#                creator = ''
#            #Оригинальное сообщение
#            if not src_lnk:
#                src_lnk = ''
#            #Не удалено
#            if not del_reason:
#                del_reason = ''
#            #Печатаем вытащенное
#            self.log_print(creator)
#            self.log_print(ctime)
#            self.log_print(txt)
#            self.log_print(code)
#            self.log_print(quotes)
#            #Делаем json
#            posts.append(jse.encode({'MsgId':msg_id,
#                                     'Creator':creator,
#                                     'Time':ctime,
#                                     'SrcLink':src_lnk,
#                                     'DelReason':del_reason,
#                                     'Txt':txt,
#                                     'Code':code,
#                                     'Quotes':quotes})
#                                    +'\n')
#        #Сохраняем топик
#        with open(out_file, "w+") as f:
#            f.writelines(posts)
#        #Выводим количество удаленных сообщений
#        return del_count
#    #--------------------------------------------------------------------------
#    def get_topic_messages(self, response):
#        """
#        Парсим топик, сохраняем сообщения
#        """
#        out_file = DATA_BASE_PATH + '/thread' + re.sub(r'/', '_', self.topic.get()) + '.txt'
#        self.deleted_msg += self.get_comments(response, out_file)
#        #Этот топик мы уже прошли
#        self.topic.pop(response.url)
#        #Обходим все страницы из self.topic
#        next_topic = self.topic.get()
#        if next_topic:
#            next_url = self.domain_name + next_topic
#            self.log_print('Will goto:', next_url)
#            sleep(4)
#            return Request(next_url, callback=self.on_topic_enter)
#        return self.logout(response)
#    #--------------------------------------------------------------------------
#    def on_topic_enter(self, response):
#        """
#        Зашли в топик, жмем кнопку "Показать удаленные сообщения"
#        """
#        self.log_print('==================================')
#        self.log_print('Topics left:', len(self.topic.urls), 'of', self.topic_n)
#        self.log_print('==================================')
#        form = response.css('form[action="%s"]'%self.topic.urls[0])
#        token = form.css('input[name="csrf"]::attr(value)').get()
#        sleep(1)
#        return FormRequest.from_response(response,
#                                         formdata={'csrf': token, 'deleted':'1'},
#                                         callback=self.get_topic_messages,
#                                         dont_filter=True)
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
