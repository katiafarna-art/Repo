"""Utility function for getting detail on run-time to raise customized exceptions"""

import inspect


def get_function_name():
    return inspect.currentframe().f_back.f_code.co_name
