import random
from datetime import datetime

from info import redis_store, constants, db
from info.libs.yuntongxun.sms import CCP
from info.models import User
from info.response_code import RET
from info.utils.captcha.captcha import captcha
from . import passport_blue
from flask import make_response, request, current_app, json, jsonify, session
import re

#退出用户
# 请求路径: /passport/logout
# 请求方式: POST
# 请求参数: 无
# 返回值: errno, errmsg
@passport_blue.route('/logout', methods=['POST'])
def logout():
    #1.清除session信息
    try:
        session.pop("user_id", None)
        session.pop("nick_name", None)
        session.pop("mobile", None)
        session.pop("is_admin", None)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="退出失败")

    #2.返回响应
    return jsonify(errno=RET.OK,errmsg="退出成功")


# 用户登陆
# 请求路径: /passport/login
# 请求方式: POST
# 请求参数: mobile,password
# 返回值: errno, errmsg
@passport_blue.route('/login', methods=['POST'])
def login():
    """
    1.获取参数
    2.校验参数,为空检验
    3.根据手机号,查询用户对象
    4.判断用户是否存在
    5.判断用户密码是否正确
    6.记录用户的登陆信息到session
    7.返回响应
    :return: 
    """
    # 1.获取参数
    mobile = request.json.get("mobile")
    password = request.json.get("password")

    
    # 2.校验参数,为空检验
    if not all([mobile,password]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不全")
    
    # 3.根据手机号,查询用户对象
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="查询用户失败")
    
    # 4.判断用户是否存在
    if not user:
        return jsonify(errno=RET.NODATA,errmsg="用户不存在")

    # if mobile == '13423682841':
    #     user.password = password
    #     db.session.add(user)
    #     db.session.commit()

    # 5.判断用户密码是否正确
    if not user.check_password(password):
        return jsonify(errno=RET.DATAERR,errmsg="密码错误")
    
    # 6.记录用户的登陆信息到session
    session["user_id"] = user.id
    session["nick_name"] = user.nick_name
    session["mobile"] = user.mobile

    # 6.1记录用户最后一次登陆时间
    user.last_login = datetime.now()
    # try:
    #     db.session.commit()
    # except Exception as e:
    #     current_app.logger.error(e)

    # 7.返回响应
    return jsonify(errno=RET.OK,errmsg="登陆成功")


# 注册用户
# 请求路径: /passport/register
# 请求方式: POST
# 请求参数: mobile, sms_code,password
# 返回值: errno, errmsg
@passport_blue.route('/register', methods=['POST'])
def register():
    """
    1.获取参数
    2.校验参数,为空校验
    3.根据手机号取出redis,短信验证码
    4.短信验证码,正确性判断
    5.创建用户对象,设置属性
    6.保存用户到数据库
    7.返回响应
    :return:
    """
    # 1.获取参数
    # json_data = request.data
    # dict_data = json.loads(json_data)
    #上面两句话,可以写成一句话,
    dict_data = request.get_json() #等价于request.json
    mobile = dict_data.get("mobile")
    sms_code = dict_data.get("sms_code")
    password = dict_data.get("password")

    # 2.校验参数,为空校验
    if not all([mobile,sms_code,password]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不全")

    # 3.根据手机号取出redis,短信验证码,并判断有效期
    try:
        redis_sms_code = redis_store.get("sms_code:%s"%mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取短信验证码失败")

    if not redis_sms_code:
        return jsonify(errno=RET.NODATA,errmsg="短信验证码已过期")

    # 4.短信验证码,正确性判断
    if sms_code != redis_sms_code:
        return jsonify(errno=RET.DATAERR,errmsg="短信验证码填写错误")

    # 5.创建用户对象,设置属性
    user = User()
    user.nick_name = mobile
    # user.password_hash = password #存储的是明文,不安全
    user.password = password #密码加密
    user.mobile = mobile

    # 6.保存用户到数据库
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg="注册失败")

    # 7.返回响应
    return jsonify(errno=RET.OK,errmsg="注册成功")


# 获取短信验证码
# 请求路径: /passport/sms_code
# 请求方式: POST
# 请求参数: mobile, image_code,image_code_id
# 返回值: errno, errmsg
@passport_blue.route('/sms_code', methods=['POST'])
def sms_code():
    """
    1.获取参数
    2.校验参数,为空检验
    3.验证码手机号格式是否正确
    4.根据图片验证码编号,取出redis图片验证码
    5.判断Redis中的图片验证码是否过期了
    6.删除redis,图片验证码
    7.正确性校验,传入的图片验证码和redis中的是否一致
    8.生成短信验证码,调用CCP对象来发送短信
    9.判断短信是否发送成功
    10.保存短信验证码到redis
    11.返回发送状态
    :return:
    """
    # 1.获取参数
    json_data = request.data
    dict_data =  json.loads(json_data)
    mobile = dict_data.get("mobile")
    image_code = dict_data.get("image_code")
    image_code_id = dict_data.get("image_code_id")

    # 2.校验参数,为空检验
    if not all([mobile,image_code,image_code_id]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不能为空")

    # 3.验证码手机号格式是否正确
    if not re.match("1[3-9]\d{9}",mobile):
        return jsonify(errno=RET.DATAERR,errmsg="手机号格式错误")

    # 4.根据图片验证码编号,取出redis图片验证码
    try:
        redis_image_code = redis_store.get("image_code:%s"%image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取图片验证码失败")

    # 5.判断Redis中的图片验证码是否过期了
    if not redis_image_code:
        return jsonify(errno=RET.NODATA,errmsg="图片验证码已过期")

    # 6.删除redis,图片验证码
    try:
        redis_store.delete("image_code:%s"%image_code_id)
    except Exception as e:
        current_app.logger.error(e)

    # 7.正确性校验,传入的图片验证码和redis中的是否一致
    if image_code.lower() != redis_image_code.lower():
        return jsonify(errno=RET.DATAERR,errmsg="图片验证码填写错误")

    # 8.生成短信验证码,调用CCP对象来发送短信
    sms_code = "%06d"%random.randint(0,999999)
    current_app.logger.debug("短信验证码是 = %s"%sms_code)
    """
    ccp = CCP()
    try:
        result = ccp.send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES/60], 1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg="云通讯发送短信异常")

    # 9.判断短信是否发送成功
    if result == -1:
        return jsonify(errno=RET.DATAERR,errmsg="发送短信失败")
    """

    # 10.保存短信验证码到redis
    try:
        redis_store.set("sms_code:%s"%mobile,sms_code,constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="短信验证码保存失败")

    # 11.返回发送状态
    return jsonify(errno=RET.OK,errmsg="发送短信成功")


#功能描述: 获取图片验证码
# 请求路径: /passport/image_code
# 请求方式: GET
# 请求参数: cur_id, pre_id
# 返回值: 图片验证码
@passport_blue.route('/image_code')
def image_code():
    """
    1.获取参数
    2.校验参数,cur_id
    3.判断是否有上个pre_id,如果有则删除redis中上次图片验证码
    4.生成图片验证码,并存储到redis中
    5.返回图片验证码
    :return:
    """
    # 1.获取参数
    cur_id = request.args.get("cur_id")
    pre_id = request.args.get("pre_id")

    # 2.校验参数,cur_id
    if not cur_id:
        return "图片验证码编号不能为空"

    # 3.判断是否有上个pre_id,如果有则删除redis中上次图片验证码
    try:
        if pre_id:
            redis_store.delete("image_code:%s"%pre_id)
    except Exception as e:
        current_app.logger.error(e)

    # 4.生成图片验证码,并存储到redis中
    name, text, image_data = captcha.generate_captcha()
    try:
        #参数格式: key, value, time
        redis_store.set("image_code:%s"%cur_id,text,constants.IMAGE_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return "存储图片失败"

    # 5.返回图片验证码
    response = make_response(image_data)
    response.headers["Content-Type"] = "image/png"
    return response