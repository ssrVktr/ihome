import json

from flask import current_app, jsonify, g, request, session
from sqlalchemy import and_
from . import api
from ihome import redis_store, constants, db
from ihome.utils.image_storage import storage
from ihome.utils.commons import RET, login_required
from ihome.models import Area, House, Facility, HouseImage, User


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


@api.route('/houses/info', methods=['POST'])
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


@api.route('/houses/image', methods=['POST'])
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


@api.route('/user/houses', methods=['GET'])
@login_required
def get_user_houses():
    """
    获取用户发布的房源信息
    :return:
    """
    user_id = g.user_id
    try:
        user = User.query.get(user_id)
        houses = user.houses
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取数据失败')

    # 将查询到的房屋数据转为字典存放到字典
    houses_list = []
    if houses:
        for house in houses:
            houses_list.append(house.to_basic_dict())
    return jsonify(errno=RET.OK, errmsg='OK', data={'houses': houses_list})


@api.route('/houses/index', methods=['GET'])
def get_house_index():
    """
    从redis中获取主页幻灯片展示的房屋图片
    :return:
    """
    try:
        ret = redis_store.get('home_page_data')
    except Exception as e:
        current_app.logger.error(e)
        ret = None
    if ret:
        # 从redis中取出的字符串中含有bytes类型，所以需要解码
        ret = ret.decode()
        current_app.logger.info('hit house index info redis')
        # 因为redis中保存的是json字符串，所以直接进行字符串拼接返回
        return '{"errno": 0, "errmsg": "ok", "data": %s}' % ret, 200, {'Content-Type': 'application/json'}
    else:
        try:
            # 查询数据库，返回房屋订单数目最多的5条数据
            houses = House.query.order_by(House.order_count.desc()).limit(constants.HOME_PAGE_MAX_HOUSES)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='查询数据失败')
        if not houses:
            return jsonify(errno=RET.NODATA, errmsg='查询无数据')

        houses_list = []
        for house in houses:
            # 如果房屋未设置主图片，则跳过
            if not house.index_image_url:
                continue
            houses_list.append(house.to_basic_dict())

        # 将数据转换为json，并保存到redis缓存
        json_houses = json.dumps(houses_list)
        try:
            redis_store.setex('home_page_data', constants.HOME_PAGE_DATA_REDIS_EXPIRES, json_houses)
        except Exception as e:
            current_app.logger.error(e)

        return '{"errno": 0, "errmsg": "ok", "data": %s}' % json_houses, 200, {'Content-Type': 'application/json'}


@api.route('/houses/<int:house_id>', methods=['GET'])
def get_house_detail(house_id):
    """
    获取房屋详情
    前端在房屋详情页面展示时，如果浏览页面的用户不是该房屋的房东，则展示预定按钮，否则不展示，
    所以需要后端返回登录用户的user_id
    尝试获取用户登录的信息，若登录，则返回给前端登录用户的user_id，否则返回user_id=-1
    :param house_id:
    :return:
    """
    user_id = session.get('user_id', '-1')

    # 效验参数
    if not house_id:
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')

    # 先从redis缓存中获取数据
    try:
        ret = redis_store.get('house_info_%s' % house_id)
    except Exception as e:
        current_app.logger.error(e)
        ret = None

    if ret:
        # 从redis中取出的字符串中含有bytes类型，所以需要解码
        ret = ret.decode()
        current_app.logger.info('hit house info redis')
        return '{"errno": 0, "errmsg": "ok", "data": {"user_id": %s, "house": %s}}' % (user_id, ret),\
            200, {"Content-Type": "application/json"}

    # 查询数据库
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")
    if not house:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    # 将房屋对象数据转换为字典
    try:
        house_data = house.to_full_dict()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据出错")

    # 存入到redis中
    json_house = json.dumps(house_data)
    try:
        redis_store.setex("house_info_%s" % house_id, constants.HOUSE_DETAIL_REDIS_EXPIRE_SECOND, json_house)
    except Exception as e:
        current_app.logger.error(e)

    resp = '{"errno":"0", "errmsg":"OK", "data":{"user_id":%s, "house":%s}}' % (user_id, json_house), \
           200, {"Content-Type": "application/json"}
    return resp
