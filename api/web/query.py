# -*- coding: utf-8 -*-
# @Time    : 4/10/2023
# @Author  : nzooherd
# @File    : query.py
# @Software: PyCharm
from functools import lru_cache

import cherrypy

from core.openai_helper import OpenAIHelper


class DictionApp(object):

    def __init__(self, openai: OpenAIHelper):
        self.openai = openai
        self.chat_id = 21052

    @cherrypy.expose
    def index(self):
        return "Hello World"

    @lru_cache
    @cherrypy.expose
    def word(self, word):
        self.query = word + "是什么意思?"
        return self.openai.get_chat_response(self.chat_id, function="diction", query=word, stream=False)
