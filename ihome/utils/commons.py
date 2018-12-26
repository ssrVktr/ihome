from werkzeug.routing import BaseConverter
import functools
from flask import session, jsonify, g
from ihome.utils.response_code import RET


class ReConverter(BaseConverter):
    """自定义正则表达式路由"""
    def __init__(self, url_map, regex):
        super(ReConverter, self).__init__(url_map)
        self.regex = regex


# 定义的验证登录状态的装饰器
def login_required(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 判断用户的登录状态
        user_id = session.get('user_id')
        # 如果用户是登录的， 执行视图函数
        if user_id:
            # 将user_id保存到g对象中，在视图函数中可以通过g对象获取保存数据
            g.user_id = user_id
            return func(*args, *kwargs)
        else:
            # 如果未登录，返回未登录的信息
            return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    return wrapper
