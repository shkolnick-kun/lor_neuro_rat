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
#TODO: Добавить еще!!!
#TODO: Добавить смайлики, развернутые на 180 градусов!!!
import re

EMOJI = {re.compile(r'[\}oOоО0\|\\]?[\:\;\%]\-?\)+'):'улыбается',
         re.compile(r'[\}oOоО0\|\\]?[\:\;\%]\-?\(+'):'грустный',
         re.compile(r'\(+\-?[\:\;\%][\{oOоО0\|\\]?'):'улыбается',
         re.compile(r'\)+\-?[\:\;\%][\{oOоО0\|\\]?'):'грустный',
         re.compile(r'[\}oOоО0\|\\]?[\:\;\%]\-?[Pb]+'):'дразнит',
         re.compile(r'[\}oOоО0\|\\]?[\:\;\%]\-?B+'):'ехидный',
         re.compile(r'[\}oOоО0\|\\]?[\:\;\%]\-?[зЗ3]+'):'обожает',
         re.compile(r'[\}oOоО0\|\\]?[\:\;\%]\-?[oOоО0]+'):'удивлен',
         re.compile(r'[oOоО0]\_+[oOоО0]'):'удивлен',
         re.compile(r'[[xX][dD]|[чЧ][вВ]]+'):'смеется',
         re.compile(r'8[=+\-+][\>3з]'):'хуй',
         re.compile(r'\([.,]\)\([.,]\)'):'сиськи',
         re.compile(r'\[:?\|\|\|+:?\]'):'старый',
         re.compile(r'!+'):'восклицание',
         re.compile(r'\?+'):'вопрос'}