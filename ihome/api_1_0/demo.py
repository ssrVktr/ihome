import logging
from . import api
from ihome import models, db
from flask import current_app, make_response


@api.route("/index")
def index():
    #print("hello")
    # logging.error()   # 记录错误信息
    # logging.warn()   # 警告
    # logging.info()   # 信息
    # logging.debug()   # 调试
    current_app.logger.error("error info")
    current_app.logger.warn("warn info")
    current_app.logger.info("info info")
    current_app.logger.debug("debug info")
    res = make_response('hello')
    return res


# logging.basicConfig(level=logging.ERROR)



