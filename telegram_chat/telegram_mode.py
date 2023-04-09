# -*- coding: utf-8 -*-
# @Time    : 3/6/2023
# @Author  : nzooherd
# @File    : telegram_mode.py
# @Software: PyCharm
class TelegramMode:

    def __init__(self):
        self.auto_reset = False

    def is_auto_reset(self) -> bool:
        """
        Determine if it is in auto reset mode.
        """
        return self.auto_reset

    def auto_reset_mode(self):
        self.auto_reset = True

    def cancel_auto_reset_mode(self):
        self.auto_reset = False

    def __repr__(self):
        return str(self.__dict__)
