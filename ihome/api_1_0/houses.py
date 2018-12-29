import json

from flask import current_app, jsonify, g, request
from sqlalchemy import and_
from . import api
from ihome import redis_store, constants, db
from ihome.utils.image_storage import storage
from ihome.utils.commons import RET, login_required
from ihome.models import Area, House, Facility, HouseImage


@api.route('/areas')
def get_area_info():
    """
    获取城区信息
    :return: 返回城区信息
    """
    try:
        resp_json = redis_store.get('area_info')
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json:
            # redis有缓存数据
            current_app.logger.info('hit redis area_info')
            return resp_json, 200, {'Content-Type': 'application/json'}

    # 查询数据库，获取城区数据
    try:
        area_li = Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')

    area_dict_li = []
    # 取出对象中的字典数据放入列表
    for area in area_li:
        area_dict_li.append(area.to_dict())

    # 将字典数据转换为json字符串
    resp_dict = dict(errno=RET.OK, errmsg='OK', data=area_dict_li)
    resp_json = json.dumps(resp_dict)

    # 将数据保存至redis中
    try:
        redis_store.setex('area_info', constants.AREA_INFO_REDIS_CACHE_EXPIRES, resp_json)
    except Exception as e:
        current_app.logger.error(e)

    return resp_json, 200, {'Content-Type': 'application/json'}


@api.route('houses/info', methods=['POST'])
@login_required
def save_house_info():
    """
    保存房屋的基本信息
    :param: 前端发来的数据
    {
        "title":"",
        "price":"",
        "area_id":"1",
        "address":"",
        "room_count":"",
        "acreage":"",
        "unit":"",
        "capacity":"",
        "beds":"",
        "deposit":"",
        "min_days":"",
        "max_days":"",
        "facility":["7","8"]
    }
    :return: 'ok'
    """
    # 获取数据
    user_id = g.user_id
    house_data = request.get_json()

    title = house_data.get("title")  # 房屋名称标题
    price = house_data.get("price")  # 房屋单价
    area_id = house_data.get("area_id")  # 房屋所属城区的id
    address = house_data.get("address")  # 房屋地址
    room_count = house_data.get("room_count")  # 房屋包含的房间数目
    acreage = house_data.get("acreage")  # 房屋面积
    unit = house_data.get("unit")  # 房屋布局（几室几厅)
    capacity = house_data.get("capacity")  # 房屋容纳人数
    beds = house_data.get("beds")  # 房屋卧床数目
    deposit = house_data.get("deposit")  # 押金
    min_days = house_data.get("min_days")  # 最小入住天数
    max_days = house_data.get("max_days")  # 最大入住天数

    # 校验参数
    if not all([title, price, area_id, address, room_count, acreage,
                unit, capacity, beds, deposit, min_days, max_days]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 判断金额是否正确
    try:
        price = int(float(price)*100)
        deposit = int(float(deposit)*100)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 判断城区id是否存在
    try:
        area = Area.query.get(area_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')

    if area is None:
        return jsonify(errno=RET.NODATA, errmsg='城区信息有误')

    # 保存房屋信息
    house = House()
    house.user_id = user_id
    house.area_id = area_id
    house.title = title
    house.price = price
    house.address = address
    house.room_count = room_count
    house.acreage = acreage
    house.unit = unit
    house.capacity = capacity
    house.beds = beds
    house.deposit = deposit
    house.min_days = min_days
    house.max_days = max_days

    # 处理房屋的设施信息
    facility_ids = house_data.get("facility")

    # 如果用户勾选了设施信息，再保存数据库
    if facility_ids:
        try:
            facilities = Facility.query.filter(Facility.id.in_(facility_ids)).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='数据库异常')
        if facilities:
            # 表示有合法的设施数据，需要保存
            house.facilities = facilities

    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')

    # 保存数据成功
    return jsonify(errno=RET.OK, errmsg='ok', data={'house_id': house.id})


@api.route('houses/image', methods=['POST'])
@login_required
def save_house_image():
    """
    保存房屋的图片
    :param: 图片数据,房屋id
    :return:图片地址
    """
    user_id = g.user_id
    image_file = request.files.get('house_image')
    house_id = request.form.get('house_id')
    if not all([image_file, house_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')

    # 判断房屋id是否正确
    try:
        house = House.query.filter(and_(House.id == house_id, House.user_id == user_id)).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')

    if house is None:
        return jsonify(errno=RET.NODATA, errmsg='房屋不存在')

    image_data = image_file.read()
    # 保存图片到七牛
    try:
        file_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='保存图片失败')

    # 保存图片地址到数据库
    house_image = HouseImage()
    house_image.house_id = house_id
    house_image.url = file_name
    db.session.add(house_image)

    # 添加房屋的主图片
    if not house.index_image_url:
        house.index_image_url = file_name
        db.session.add(house)
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存图片数据库异常')

    image_url = constants.QINIU_URL_DOMAIN + file_name
    return jsonify(errno=RET.OK, errmsg='ok', data={'image_url': image_url})
