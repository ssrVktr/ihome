import re

from flask import g, current_app, jsonify, request, session
from sqlalchemy.exc import IntegrityError
from . import api
from ihome.utils.commons import login_required
from ihome.utils.response_code import RET
from ihome.utils.image_storage import storage
from ihome.models import User
from ihome import db, constants


@api.route('/user', methods=['GET'])
@login_required
def get_user_profile():
    """
    获取用户信息
    :return: 用户信息
    """
    # 在登录装饰器中已设置g对象的user_id属性
    user_id = g.user_id

    # 获取用户信息
    try:
        user = User.query.filter_by(id=user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='用户查询失败')
    if user is None:
        return jsonify(errno=RET.NODATA, errmsg='无效操作')

    return jsonify(errno=RET.OK, errmsg='ok', data=user.to_dict())


@api.route('/users/avatar', methods=['POST'])
@login_required
def set_user_avatar():
    """
    设置用户头像
    :param: 图片数据，多媒体表单
    :return: 头像地址
    """
    # 装饰器的代码中已经将user_id保存到g对象中，所以视图中可以直接读取
    user_id = g.user_id

    # 获取图片数据
    image_file = request.files.get('avatar')
    if image_file is None:
        return jsonify(errno=RET.PARAMERR, errmsg='未上传图片')
    image_data = image_file.read()

    # 调用七牛云上传图片，返回文件名
    try:
        file_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='闪传图片失败')

    # 保存文件名（图片地址）到数据库
    try:
        User.query.filter_by(id=user_id).update({'avatar_url': file_name})
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存图片信息失败')

    avatar_url = constants.QINIU_URL_DOMAIN + file_name
    # 保存成功返回
    return jsonify(errno=RET.OK, errmsg='保存成功', data={'avatar_url': avatar_url})


@api.route('/users/name', methods=['PUT'])
@login_required
def set_user_name():
    """
    更新用户昵称
    :param: 用户输入的新昵称
    :return: json 修改成功的新昵称
    """
    # 装饰器的代码中已经将user_id保存到g对象中，所以视图中可以直接读取
    user_id = g.user_id

    # 获取参数
    req_data = request.get_json()
    new_user_name = req_data.get('new_user_name')

    # 验证参数
    if not re.match(r'\w{2,32}', new_user_name):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不正确')

    # 获取用户数据
    try:
        user = User.query.filter_by(id=user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='用户查询错误')

    # 利用数据库约束unique抛出的异常判断用户名是否已存在(减少数据库查询次数)
    user.name = new_user_name
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAEXIST, errmsg='用户名已存在')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='用户名保存出错')

    # 修改session中的name
    session['name'] = user.name

    # 返回新用户昵称
    return jsonify(errno=RET.OK, errmsg='保存成功', data={'new_user_name': user.name})


@api.route('/users/auth', methods=['GET'])
@login_required
def get_user_auth():
    """
    获取用户实名认证信息
    :return: 用户真实姓名，证件号
    """
    user_id = g.user_id

    # 获取信息
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取用户实名信息失败')

    if user is None:
        return jsonify(errno=RET.NODATA, errmsg='无效操作')

    return jsonify(errno=RET.OK, errmsg='ok', data=user.auth_to_dict())


@api.route('/users/auth', methods=['POST'])
@login_required
def set_user_auth():
    """
    保存实名认证信息
    :return:
    """
    user_id = g.user_id

    # 获取参数
    req_data = request.get_json()
    if not req_data:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    real_name = req_data.get('real_name')
    id_card = req_data.get('id_card')

    # 效验参数
    if not all([real_name, id_card]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')

    # 保存用户的姓名和证件号
    try:
        User.query.filter_by(
            id=user_id, real_name=None, id_card=None).update(
            {'real_name': real_name, 'id_card': id_card})
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存用户实名信息失败')
    return jsonify(errno=RET.OK, errmsg='ok')
