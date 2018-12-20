from . import api
from ihome.utils.captcha.captcha import captcha
from ihome import redis_store, constants
from flask import current_app, make_response, jsonify
from ihome.utils.response_code import RET


# GET 127.0.0.1/api/v1.0/image_codes/<image_code_id>
@api.route('/image_codes/<image_code_id>')
def get_image_code(image_code_id):
    """
    获取图片验证码
    :param image_code_id:
    :return:
    """
    # 名字，真实文本， 图片数据
    name, text, image_data = captcha.generate_captcha()
    # redis单条维护记录，选用字符串
    # "image_code_编号1": "真实值"
    try:
        redis_store.setex('image_code_%s' % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify({'errno': RET.DBERR, 'errmsg': '保存图片验证码失败'})

    res = make_response(image_data)
    res.headers['Content-Type'] = 'image/jpg'
    return res
