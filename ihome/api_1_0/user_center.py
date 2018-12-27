from flask import jsonify, session

from . import api
from ihome.utils.commons import login_required, RET


@api.route('users/center', methods=['get'])
@login_required
def get_user_profile():
    """
    获取用户昵称和手机号
    :return: 用户昵称和手机号
    """

    # 从session中获取用户名和手机号
    user_name = session.get('name')
    mobile = session.get('mobile')
    return jsonify(
        errno=RET.OK, errmsg='成功', data={
            'user_name': user_name,
            'mobile': mobile
        }
    )
