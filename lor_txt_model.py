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
import json

from keras.preprocessing.text import text
from keras.preprocessing.sequence import pad_sequences
from keras.models import load_model
#==============================================================================
class LORTxtModel():
    """
    Обертка над моделью keras
    """
    def __init__(self, tokenizer_fname, model_fname, max_len, batch_size):
        """
        tokenizer_fname - имя файла токенизатора
        model_fname - имя файла модели
        """
        self.max_len = max_len
        self.batch_size = batch_size
        #Токенизатор
        with open(tokenizer_fname, 'r') as f:
            self.tok = text.tokenizer_from_json(json.load(f))
        #Модель
        self.mdl = load_model(model_fname)
        self.mdl._make_predict_function()
    #--------------------------------------------------------------------------
    def predict(self, X):
        """
        X - список со списакми токенов текстов
        Возвращает результаты работы модели с текстами из X
        """
        X_str = [' '.join(tokens) for tokens in X]
        X_seq = self.tok.texts_to_sequences(X_str)
        X_seq = pad_sequences(X_seq, maxlen=self.max_len)
        return self.mdl.predict(X_seq, verbose=0, batch_size=self.batch_size)