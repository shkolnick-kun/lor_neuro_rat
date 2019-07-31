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
import pickle as pk
import re
from time import sleep

from scrapy.http import Request

from lor_spider_base import LORSpiderBase

import lorcfg as cfg

class LORUrlBuf():
    """
    URL buffer class.
    """
    def __init__(self, fname):
        self.fname = fname
        try:
            with open(fname, 'rb') as f:
                self.urls = pk.load(f)
            self.urls.sort()
            self.sorted = True
        except Exception as e:
            print(e)
            self.urls = []
            self.sorted = False
    #==========================================================================
    def append(self, url):
        """
        Append a url to buffer
        """
        self.sorted = False
        #
        url = str(url)
        #
        if url not in self.urls:
            self.urls.append(url)
    #==========================================================================
    def get(self):
        """
        Get current URL-list head
        """
        if not self.urls:
            return ''
        #
        if not self.sorted:
            self.urls.sort()
        #
        return self.urls[0]
    #==========================================================================
    def dump(self):
        """
        Dump URL-list to disk
        """
        if not self.sorted:
            self.urls.sort()
        #
        with open(self.fname, 'wb+') as f:
            pk.dump(self.urls, f)
    #==========================================================================
    def pop(self, url):
        """
        Pop the head of URL-list
        """
        if not self.sorted:
            self.urls.sort()
        #
        url = str(url)
        #
        if self.urls[0] not in url:
            raise ValueError
        #
        self.urls.remove(self.urls[0])
        self.dump()
###############################################################################
class LORSpider(LORSpiderBase):
    """
    TODO: Сделать скрипт более устойчивым к преждевременным остановкам

    1. Научиться обходит "автобаны" с помощью списков проксей.
    Списко проксей можно формировать отдельным скриптом.
    """
    name = 'GetLOR'

    arch = []
    arch_n = 0
    topic = []
    topic_n = 0
    deleted_msg = 0
    #==========================================================================
    def __init__(self, name=None, **kwargs):
        LORSpiderBase.__init__(self, name, **kwargs)
        #
        self.arch = LORUrlBuf(cfg.PARSER_BASE_PATH + '/arch.pkl')
        self.topic = LORUrlBuf(cfg.PARSER_BASE_PATH + '/topic.pkl')
        #
        with open('arch_urls.txt', 'r') as f:
            start_urls = f.readlines()
            self.arch_n = len(start_urls)
            if not self.arch.urls and not self.topic.urls:
                for url in start_urls:
                    self.arch.append(url[:-1])
                #Dump all the urls
                self.arch.dump()
        try:
            with open(cfg.PARSER_BASE_PATH + '/topic_num.pkl', 'rb') as f:
                n = pk.load(f)
                self.topic_n = max(n, len(self.topic.urls))
        except Exception as e:
            print(e)
    #==========================================================================
    def on_login(self, response):
        if self.has_logged_in(response):
            #Не закончили траверс архива
            if self.arch.urls:
                return Request(self.domain_name + self.arch.get(), callback=self.on_arch_enter)
            #Не закончили траверс списка топиков
            if self.topic.urls:
                return Request(self.domain_name + self.topic.get(), callback=self.on_topic_enter)
            #Данные уже скачаны!!!
            return None
        return None
    #==========================================================================
    def on_arch_enter(self, response):
        """
        Парсим страницы архива, форомируем список URL-ов для топиков
        """
        self.log_print('==================================')
        self.log_print('Arch left:', len(self.arch.urls), 'of', self.arch_n)
        self.log_print('==================================')
        msgtable = response.css('table[class="message-table"]')
        for l in msgtable.css('a::attr(href)').getall():
            if 'user-filter' in l or 'page' in l:
                continue
            l = l.split('?')[0]
            if l not in self.topic.urls:
                self.topic.append(l)
                self.topic.dump()
        #
        next_page = response.css('a[rel="next"]::attr(href)').get()
        if next_page:
            sleep(4)
            self.log_print('Will goto:', next_page)
            return Request(self.domain_name + next_page, callback=self.on_arch_enter)
        #
        self.arch.pop(response.url)
        #Обходим все страницы из self.arch.urls
        next_page = self.arch.get()
        if next_page:
            next_url = self.domain_name + next_page
            self.log_print('Will goto:', next_url)
            sleep(4)
            return Request(next_url, callback=self.on_arch_enter)
        #Сохраняем список топиков
        self.topic.dump()
        self.topic_n = len(self.topic.urls)
        #Сохраняем общее количество топиков
        with open(cfg.PARSER_BASE_PATH + '/topic_num.pkl', 'wb+') as f:
            pk.dump(self.topic_n, f)
        #Теперь обходим топики
        self.log_print('Will visit topics...')
        next_url = self.domain_name + self.topic.get()
        return Request(next_url, callback=self.on_topic_enter)
    #==========================================================================
    def go_next(self, response):
        #Обходим все страницы из self.topic
        next_topic = self.topic.get()
        if next_topic:
            next_url = self.domain_name + next_topic
            self.log_print('Will goto:', next_url)
            sleep(4)
            return Request(next_url, callback=self.on_topic_enter)
        return self.logout(response)
    #--------------------------------------------------------------------------
    def on_topic_enter(self, response):
        """
        Парсим топик, сохраняем сообщения
        """
        return self.topic_enter_handler(response, self.topic.urls)
    #--------------------------------------------------------------------------
    def get_topic_messages(self, response):
        """
        Парсим топик, сохраняем сообщения
        """
        topic_data = self.get_comments(response)
        out_file = cfg.PARSER_BASE_PATH + '/topic'
        out_file += re.sub(r'/', '_', self.topic.urls[0]) + '.pkl'
        topic_data.to_pickle(out_file)

        self.deleted_msg += len(topic_data[topic_data['DelReason'] != ''])
        #Этот топик мы уже прошли
        self.topic.pop(response.url)
        
        return self.go_next(response)
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
