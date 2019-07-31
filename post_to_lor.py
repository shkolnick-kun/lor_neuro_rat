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
import os
import pickle as pk
import re
from time import sleep

import numpy as np
import pandas as pd

from scrapy.http import Request, FormRequest

from clean_text import data_prepare
from lor_txt_model import LORTxtModel

from lor_spider_base import LORSpiderBase

import lorcfg as cfg
###############################################################################
class LORModels():
    """
    Обертка над всеми моделями LOR + утилиты
    """
    def __init__(self):
        #Бинарный классификатор
        self.bin_cls = LORTxtModel(cfg.BIN_TOKENIZER, cfg.BIN_CLASSIFIER, 
                                   cfg.MAX_LEN, cfg.BATCH_SIZE)
        #Модель категоризации
        self.cat_cls = LORTxtModel(cfg.CAT_TOKENIZER, cfg.CAT_CLASSIFIER,
                                   cfg.MAX_LEN, cfg.BATCH_SIZE)
        with open(cfg.CAT_LIST, 'rb') as f:
            self.cat_list = pk.load(f)
    #--------------------------------------------------------------------------
    def find_suspicious(self, X):
        """
        Поиск подозрителдьных постов
        Принимает - датафрейм с постами
        Выдает - датафрейм с подозрительными постами (если их нет - пустой датафрейм)
        """
        y = self.bin_cls.predict(list(X['Tokens']))
        X['BinProb'] = y
        return X[y > cfg.BIN_THR].copy()
    #--------------------------------------------------------------------------
    def get_top3(self, x):
        """
        Сформировать часть отчета с категориями подозрительных постов.

        Принимает результат работы категориального классификатора.
        Выдает строку с топ-3 категорий.
        """
        top3 = ''
        for i in range(3):
            c = np.argmax(x)
            top3 += ' **' + str(self.cat_list[c]) + '**(%.2f)'%x[c]
            x[c] = 0
        return top3
    #--------------------------------------------------------------------------
    def cat_suspicious(self, X):
        """
        Категоризация подозрительных постов

        Принимает датафрейм с подозрительными постами
        Возвращает его же с добавленным столбцом с топ-3 категорий.
        """
        y = self.cat_cls.predict(list(X['Tokens']))
        X['CatRes'] = pd.Series(['']*len(X))
        for i in range(len(X)):
            X.at[i, 'CatRes'] = self.get_top3(y[i])
        return X
###############################################################################
def merge_topic_versions(old, new):
    """
    Слияние старогй и новой версии сообщений топика
    Принимает:
        old - сарая версия топика (датафрейм)
        new - новая версия топика (датафрейм)
    Возвращает:
        результат слияния (датафрейм)
        обновленные/новые посты (датафрейм)
    """
    merge = pd.merge(old[['MsgId', 'Txt', 'Code', 'Quotes']], new,
                     how='outer',
                     on='MsgId',
                     suffixes=('_old', '_new'),
                     indicator=False)

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
    merge.drop(drop_list, axis=1, inplace=True)

    return merge, merge[update].copy()
###############################################################################
class LORTopic():
    """
    Описание топика при его обновлении
    """
    def __init__(self, url, mod_time):
        self.url = url
        self.mod_time = mod_time
    #--------------------------------------------------------------------------
    def update(self, mod_time):
        """
        Обновление информации о топике
        Принимает:
            время модификации
        Возвращает:
            список с URL топика, если топик был модифицирован,
            либо пустой список
        """
        if self.mod_time != mod_time:
            self.mod_time = mod_time
            return [self.url]
        return []
    #--------------------------------------------------------------------------
    def dump(self):
        return {'URL': self.url, 'ModTime': self.mod_time}
###############################################################################
TRACKER_DUMP_PATH = cfg.BOT_BASE_PATH + '/traker.pkl'
class LORTracker():
    """
    Трекер - нужен для отслеживания изменений в трекере LOR.
    """
    topic = []
    url = []
    def __init__(self):
        try:
            with open(TRACKER_DUMP_PATH, 'rb') as f:
                for rec in pk.load(f):
                    self.url.append(rec['URL'])
                    self.topic.append(LORTopic(rec['URL'], rec['ModTime']))
        except Exception as e:
            print(e)
    #--------------------------------------------------------------------------
    def dump(self):
        """
        Сохранение трекера в файл
        """
        d = [t.dump() for t in self.topic]
        with open(TRACKER_DUMP_PATH, 'wb+') as f:
            pk.dump(d, f)
    #--------------------------------------------------------------------------
    def update(self, topic_url, mod_time):
        """
        Обновить информацию о топике
        Принимает:
            topic_url - URL топика
            mod_time - Время модификации топика
        Возвращает:
            список с URL топика, если топик был модифицирован/новый,
            либо пустой список
        """
        if topic_url not in self.url:
            self.url.append(topic_url)
            self.topic.append(LORTopic(topic_url, mod_time))
            return [topic_url]
        return self.topic[self.url.index(topic_url)].update(mod_time)
###############################################################################
class LORSpider(LORSpiderBase):
    """
    TODO: Сделать скрипт более устойчивым к преждевременным остановкам

    1. Научиться обходит "автобаны" с помощью списков проксей.
    Списко проксей можно формировать отдельным скриптом.
    """
    name = 'NeuroRat'
    tracker_page = LORSpiderBase.domain_name + '/tracker/?filter=all'
    report_page = LORSpiderBase.domain_name + '/add_comment.jsp?topic=%s'%cfg.REPORT_TO
    #
    mdls = LORModels()
    #
    suspicious = []
    susp_len = 0
    susp_num = 0
    report = []
    msg_num = 0
    #
    tracker = LORTracker()
    topic = []
    update = 10
    #==========================================================================
    def __init__(self, name=None, **kwargs):
        LORSpiderBase.__init__(self, name, **kwargs)
    #==========================================================================
    def on_login(self, response):
        """
        После удачного входа на сайт - переходим к трекеру
        """
        if self.has_logged_in(response):
            return Request(self.tracker_page, callback=self.on_tracker_enter)
        return None
    #==========================================================================
    def go_next(self, response):
        """
        Логика переходов между состояниями
        """
        sleep(4)
        if self.report:
            #Постим сообщение
            return Request(self.report_page,
                           callback=self.on_report_form_enter,
                           dont_filter=True)
        #Обходим все страницы из self.topic
        if self.topic:
            next_topic = self.topic[0]
            next_url = self.domain_name + next_topic
            self.log_print('Will goto:', next_url)
            return Request(next_url,
                           callback=self.on_topic_enter,
                           dont_filter=True)
        #Топики кончились, сохраняем дамп трекера
        self.tracker.dump()
        #Идем...
        if cfg.ONE_SHOT:
            #На выход
            return self.logout(response)
        #Или опять в трекер
        return Request(self.tracker_page,
                       callback=self.on_tracker_enter,
                       dont_filter=True)
    #==========================================================================
    def on_tracker_enter(self, response):
        """
        Парсим страницы трекера, форомируем список URL-ов для топиков
        """
        self.log_print('==================================')
        if self.susp_len > 0:
            #Постим сообщение
            return Request(self.report_page,
                           callback=self.on_report_form_enter,
                           dont_filter=True)
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
            #Обновление информации трекера
            self.log_print(topic_url)
            mod_time = row.css('td[class="dateinterval"]').css('time::attr(datetime)').get()
            page_topic += self.tracker.update(topic_url, mod_time)
        #
        if page_topic:
            #Пополняеем список топиков
            self.topic += page_topic
            #Переходим к следующей странице трекера
            for ref in response.css('div[class="nav"]').css('a[href*="?offset="]'):
                if 'следующие' in ref.css('::text').get():
                    sleep(4)
                    next_page = ref.css('::attr(href)').get()
                    self.log_print('Will goto:', next_page)
                    return Request(self.domain_name + next_page,
                                   callback=self.on_tracker_enter,
                                   dont_filter=True)
        #Переход дальше
        sleep(6)
        return self.go_next(response)
    #==========================================================================
    def on_report_form_enter(self, response):
        """
        Формирование и отправка отчета.
        Если отчет получается длинный - отправляем кусками по 40- ссылок.
        """
        if self.suspicious:
            #Формируем отчет
            susp = pd.concat(self.suspicious, ignore_index=True, copy=True, sort=False)
            self.suspicious = []
            self.susp_len = 0
            #Делаем категоризацию постов
            susp = self.mdls.cat_suspicious(susp)
            #
            self.log_print('+++++++++++++++++++++++++++++++++++')
            self.log_print(list(susp['MsgId']))
            self.log_print('+++++++++++++++++++++++++++++++++++')
            #
            susp.sort_values(by=['BinProb'], inplace=True, ascending=False)
            susp.reset_index(inplace=True, drop=True)
            #
            msg_ids = list(susp['MsgId'])
            top_ids = list(susp['TopId'])
            cls_prob = list(susp['BinProb'])
            cat_prob = list(susp['CatRes'])
            #
            for i, msg in enumerate(msg_ids):
                url = top_ids[i]
                if 'topic' not in msg:
                    url += '?cid=' + msg.split('-')[1]
                r = ' * ' + url + ' (p=%.2f)'%cls_prob[i] + cat_prob[i] + '\n'
                self.report.append(r)
        #Отправка отчета кусками
        form = response.css('form[action="/add_comment.jsp"]')
        if form:
            self.log_print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')
            self.log_print(len(self.report))
            self.log_print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')
            #
            report = 'Проверено: %d, Подозрительных: %d\n\n'%(self.msg_num, self.susp_num)
            report += 'Подозрительные сообщения:\n'
            for i in range(min(40, len(self.report))):
                report += self.report.pop(0)
            #Отправляем отчет
            sleep(4)
            token = form.css('input[name="csrf"]::attr(value)').get()
            topic = form.css('input[name="topic"]::attr(value)').get()
            replyto = form.css('input[name="replyto"]::attr(value)').get()
            self.log_print(token, topic, replyto)
            data = {'csrf': token,
                    'topic': topic,
                    'replyto': replyto,
                    'mode':'markdown',
                    'title':'Нейроябеда',
                    'msg':report}
            return FormRequest.from_response(response,
                                             formdata=data,
                                             callback=self.go_next,
                                             dont_filter=True)
        #
        self.log_print('Не удалось запостить!!!')
        return self.logout(response)
    #==========================================================================
    def on_topic_enter(self, response):
        """
        Парсим топик, сохраняем сообщения
        """
        return self.topic_enter_handler(response, self.topic)
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
            #Перед использованием приводим данные "в порядок"
            classify_data.reset_index(inplace=True, drop=True)
            #Инкремент счетчика проверенных сообщений
            self.msg_num += len(classify_data)
            self.log_print(classify_data.head())
            #Подготовка данных
            classify_data = data_prepare(classify_data, verbous=False).copy()
            #Классификация данных
            cls_res = self.mdls.find_suspicious(classify_data)
            #Анализ результатов
            if len(cls_res) > 0:
                self.suspicious.append(cls_res)
                self.susp_len += len(cls_res)
                self.susp_num += len(cls_res)
                #Если "подозрителдьных" сразу много - переходим к отправке отчета
                if self.susp_len > 40:
                    sleep(4)
                    return Request(self.report_page,
                                   callback=self.on_report_form_enter,
                                   dont_filter=True)
        #Переход к следующему состоянию
        return self.go_next(response)
###############################################################################
if __name__ == '__main__':
    from scrapy.crawler import CrawlerProcess

    PROCESS = CrawlerProcess({'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'})

    PROCESS.crawl(LORSpider)
    PROCESS.start()
    PROCESS.join()
else:
    SPIDER = LORSpider()
