from datetime import datetime
from typing import Union


def default(obj):
    if isinstance(obj, datetime.date):
        return obj.strftime('%Y-%m-%d')
    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')


def error(*, code=-1, message="fail"):
    return {
        'code': code,
        'msg': message,
        'data': "",
    }


def ok(*, code=0, data=None, message="Operation successful"):
    return {
        'code': code,
        'msg': message,
        'data': data
    }


def page(*, code=0, total=0, rows: Union[list, dict, str] = None, message="Operation successful"):
    return {
        'code': code,
        'msg': message,
        'count': total,
        'data':  rows
    }
