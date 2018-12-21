import random
from . import api
from ihome.utils.captcha.captcha import captcha
from ihome import redis_store, constants, db
from flask import current_app, make_response, jsonify, request
from ihome.utils.response_code import RET
from ihome.models import User
from ihome.libs.yuntongxun.sms import CCP


# GET 127.0.0.1/api/v1.0/image_codes/<image_code_id>
@api.route('/image_codes/<image_code_id>')
def get_image_code(image_code_id):
    """
    获取图片验证码
    :param image_code_id: 前端生成的图片uuid
    :return: 验证码图片
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


# GET /api/v1.0/sms_codes/<mobile>?image_code=xxxx&image_code_id=xxxx
@api.route("sms_codes/<re(r'1[34578]\d{9}'):mobile>")
def get_sms_code(mobile):
    """
    获取短信验证码
    :param mobile: 注册用手机号
    :return: json字符串{'errno':'xxx', 'errmsg': 'xxx'}
    """
    # 获取数据
    image_code = request.args.get('image_code', '')
    image_code_id = request.args.get('image_code_id', '')

    # 验证数据完整性
    if not all([image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')

    # 从redis中取出真实的验证码
    try:
        real_image_code = redis_store.get('image_code_%s' % image_code_id)
        real_image_code = real_image_code.decode()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='redis数据库异常')

    # 判断图片验证码是否过期
    if real_image_code is None:
        # 表示图片验证码不存在或者过期
        return jsonify(errno=RET.NODATA, errmsg='验证码已失效')

    # 删除redis中的图片验证码，防止用户使用同一个图片验证码多次验证
    try:
        redis_store.delete('image_code_%s' % image_code_id)
    except Exception as e:
        current_app.logger.error(e)

    # 与用户填写的值进行对比
    print(real_image_code, '---', image_code)
    print(type(real_image_code))
    if real_image_code.lower() != image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg='图片验证码错误')

    # 判断对于这个手机号的操作，在60秒内有没有之前的记录，如果有，则认为用户操作频繁，不接受处理
    try:
        send_flag = redis_store.get('send_sms_code_%s' % mobile)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if send_flag:
            # 表示在60秒之前有过发送的记录
            return jsonify(errno=RET.REQERR, errmssg='请求过于频繁，请60秒后重试')

    # 判断手机号是否存在
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
    else:
        if user:
            return jsonify(errno=RET.DATAEXIST, errmsg='手机号已存在')

    # 如果手机号不存在，则生成短信验证码
    sms_code = "%06d" % random.randint(0, 999999)

    # 保存真实的短信验证码
    try:
        redis_store.setex('sms_code_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # 保存发送给这个手机号的记录，防止用户在60s内再次出发发送短信的操作
        redis_store.setex('send_sms_code_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存短信验证码异常')

    # 发送短信
    try:
        ccp = CCP()
        result = ccp.send_template_sms(mobile, [sms_code,int(constants.SMS_CODE_REDIS_EXPIRES/60)],1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='发送异常')

    # 返回值
    if result == 0:
        # 发送成功
        return jsonify(errno=RET.OK, errmsg='发送成功')
    else:
        return jsonify(errno=RET.THIRDERR, errmsg='发送失败')











