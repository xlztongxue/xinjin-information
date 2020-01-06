from info import constants, db
from info.models import News, Category
from info.response_code import RET
from info.utils.commons import user_login_data
from info.utils.image_storage import image_storage
from . import profile_blue
from flask import render_template, g, redirect, request, jsonify, current_app

# 获取我的关注
# 请求路径: /user/user_follow
# 请求方式: GET
# 请求参数:p
# 返回值: 渲染user_follow.html页面,字典data数据
@profile_blue.route('/user_follow')
@user_login_data
def user_follow():
    """
    - 1.获取参数
    - 2.参数类型转换
    - 3.分页查询用户发布的新闻
    - 4.获取分页对象属性,总页数,当前页,当前页新闻列表
    - 5.新闻列表转成,字典列表
    - 6.携带数据,渲染页面
    :return:
    """
    # - 1.获取参数
    page = request.args.get("p","1")

    # - 2.参数类型转换
    try:
        page = int(page)
    except Exception as e:
        page = 1

    # - 3.分页查询用户关注的人
    try:
        paginate = g.user.followed.paginate(page,2,False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取用户失败")

    # - 4.获取分页对象属性,总页数,当前页,当前页用户列表
    totalPage = paginate.pages
    currentPage = paginate.page
    items = paginate.items

    # - 5.用户列表转成,字典列表
    user_list = []
    for item in items:
        user_list.append(item.to_dict())

    # - 6.携带数据,渲染页面
    data = {
        "totalPage":totalPage,
        "currentPage":currentPage,
        "authors":user_list
    }
    return render_template("news/user_follow.html",data=data)


# 用户新闻列表
# 请求路径: /user/news_list
# 请求方式:GET
# 请求参数:p
# 返回值:GET渲染user_news_list.html页面
@profile_blue.route('/news_list')
@user_login_data
def news_list():
    """
    - 1.获取参数
    - 2.参数类型转换
    - 3.分页查询用户发布的新闻
    - 4.获取分页对象属性,总页数,当前页,当前页新闻列表
    - 5.新闻列表转成,字典列表
    - 6.携带数据,渲染页面
    :return:
    """
    # - 1.获取参数
    page = request.args.get("p","1")

    # - 2.参数类型转换
    try:
        page = int(page)
    except Exception as e:
        page = 1

    # - 3.分页查询用户发布的新闻
    try:
        paginate = News.query.filter(News.user_id == g.user.id).order_by(News.create_time.desc()).paginate(page,3,False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取新闻失败")

    # - 4.获取分页对象属性,总页数,当前页,当前页新闻列表
    totalPage = paginate.pages
    currentPage = paginate.page
    items = paginate.items

    # - 5.新闻列表转成,字典列表
    news_list = []
    for item in items:
        news_list.append(item.to_review_dict())

    # - 6.携带数据,渲染页面
    data = {
        "totalPage":totalPage,
        "currentPage":currentPage,
        "news":news_list
    }
    return render_template("news/user_news_list.html",data=data)



# 获取/设置,新闻发布
# 请求路径: /user/news_release
# 请求方式:GET,POST
# 请求参数:GET无, POST ,title, category_id,digest,index_image,content
# 返回值:GET请求,user_news_release.html, data分类列表字段数据, POST,errno,errmsg
@profile_blue.route('/news_release', methods=['GET', 'POST'])
@user_login_data
def news_release():
    """
    1.判断是否是GET请求
    2.获取参数
    3.校验参数
    4.上传图像
    5.创建新闻对象,设置属性
    6.保存新闻到数据库
    7.返回响应
    :return:
    """
    # 1.判断是否是GET请求
    if request.method == "GET":

        #查询分类数据
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR,errmsg="获取分类失败")

        category_list = []
        for category in categories:
            category_list.append(category.to_dict())

        #携带分类数据渲染页面
        return render_template("news/user_news_release.html",categories = category_list)

    # 2.获取参数
    title = request.form.get("title")
    category_id = request.form.get("category_id")
    index_image = request.files.get("index_image")
    digest = request.form.get("digest")
    content = request.form.get("content")

    # 3.校验参数
    if not all([title,category_id,index_image,digest,content]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不全")

    # 4.上传图像
    try:
        #读取图片为二进制上传
        image_name = image_storage(index_image.read())
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg="七牛云异常")

    if not image_name: return jsonify(errno=RET.NODATA,errmsg="上传失败")

    # 5.创建新闻对象,设置属性
    news = News()
    news.title = title
    news.source = g.user.nick_name
    news.digest = digest
    news.content = content
    news.index_image_url = constants.QINIU_DOMIN_PREFIX + image_name
    news.category_id = category_id
    news.user_id = g.user.id
    news.status = 1 #1代表审核中

    # 6.保存新闻到数据库
    try:
        db.session.add(news)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg="发布新闻失败")

    # 7.返回响应
    return jsonify(errno=RET.OK,errmsg="发布成功")



# 获取新闻收藏列表
# 请求路径: /user/collection
# 请求方式:GET
# 请求参数:p(页数)
# 返回值: user_collection.html页面
@profile_blue.route('/collection')
@user_login_data
def collection():
    """
    1.获取参数
    2.参数类型转换
    3.分页查询,每页10条
    4.取出分页对象属性,总页数,当前页,当前页对象列表
    5.拼接数据,渲染页面
    :return:
    """
    # 1.获取参数
    page = request.args.get("p","1")

    # 2.参数类型转换
    try:
        page = int(page)
    except Exception as e:
        page = 1

    # 3.分页查询,每页10条
    try:
        paginate = g.user.collection_news.order_by(News.create_time.desc()).paginate(page,2,False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取新闻失败")

    # 4.取出分页对象属性,总页数,当前页,当前页对象列表
    totalPage = paginate.pages
    currentPage = paginate.page
    items = paginate.items

    #5.将对象列表转成字典列表
    news_list = []
    for item in items:
        news_list.append(item.to_dict())

    # 5.拼接数据,渲染页面
    data = {
        "totalPage":totalPage,
        "currentPage":currentPage,
        "news":news_list
    }
    return render_template("news/user_collection.html",data=data)

# 获取/设置,用户头像上传
# 请求路径: /user/pic_info
# 请求方式:GET,POST
# 请求参数:无, POST有参数,avatar
# 返回值:GET请求: user_pci_info.html页面,data字典数据, POST请求: errno, errmsg,avatar_url
@profile_blue.route('/pic_info', methods=['GET', 'POST'])
@user_login_data
def pic_info():
    """
    1.判断请求方式
    2,获取参数
    3.校验参数,为空校验
    4.上传图片,判断是否上传成功
    5.设置图片到用户对象
    6.返回响应,携带图片
    :return:
    """
    # 1.判断请求方式
    if request.method == "GET":
        return render_template("news/user_pic_info.html",user=g.user.to_dict())

    # 2,获取参数
    avatar = request.files.get("avatar")

    # 3.校验参数,为空校验
    if not avatar:
        return jsonify(errno=RET.PARAMERR,errmsg="参数不全")

    # 4.上传图片,判断是否上传成功
    try:
        image_name = image_storage(avatar.read())
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg="七牛云上传异常")

    if not image_name: return jsonify(errno=RET.DATAERR,errmsg="上传失败")

    # 5.设置图片到用户对象
    try:
        g.user.avatar_url = image_name
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="修改图片失败")

    # 6.返回响应,携带图片
    data = {
        "avatar_url":constants.QINIU_DOMIN_PREFIX + image_name
    }
    return jsonify(errno=RET.OK,errmsg="上传成功",data=data)


# 获取/设置用户密码
# 请求路径: /user/pass_info
# 请求方式:GET,POST
# 请求参数:GET无, POST有参数,old_password, new_password
# 返回值:GET请求: user_pass_info.html页面 , POST请求: errno, errmsg
@profile_blue.route('/pass_info', methods=['GET', 'POST'])
@user_login_data
def pass_info():
    """
    1.判断请求方式,是否是GET
    2.获取参数
    3.校验参数,为空校验
    4.判断旧密码是否正确
    5.判断新旧,密码是否一致
    6.设置新密码
    7.返回响应
    :return:
    """
    # 1.判断请求方式,是否是GET
    if request.method == "GET":
        return render_template("news/user_pass_info.html")

    # 2.获取参数
    old_password = request.json.get("old_password")
    new_password = request.json.get("new_password")

    # 3.校验参数,为空校验
    if not all([old_password,new_password]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不全")

    # 4.判断旧密码是否正确
    if not g.user.check_password(old_password):
        return jsonify(errno=RET.DATAERR,errmsg="旧密码不正确")

    # 5.判断新旧,密码是否一致
    if old_password == new_password:
        return jsonify(errno=RET.DATAERR,errmsg="新旧密码不能一样")

    # 6.设置新密码
    try:
        g.user.password = new_password
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="修改失败")

    # 7.返回响应
    return jsonify(errno=RET.OK,errmsg="修改成功")


# 获取/设置用户基本信息
# 请求路径: /user/base_info
# 请求方式:GET,POST
# 请求参数:POST请求有参数,nick_name,signature,gender
# 返回值:errno,errmsg
@profile_blue.route('/base_info', methods=['GET', 'POST'])
@user_login_data
def base_info():
    #1.判断是否是GET请求
    if request.method == "GET":
        return render_template("news/user_base_info.html",user=g.user.to_dict())

    #2.如果是POST请求,获取参数
    nick_name = request.json.get("nick_name")
    signature = request.json.get("signature")
    gender = request.json.get("gender")

    #3.校验参数,为空校验
    if not all([nick_name,signature,gender]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不全")

    #4.判断性别是否符合常理
    if not gender in ["MAN","WOMAN"]:
        return jsonify(errno=RET.DATAERR,errmsg="性别异常")

    #5.修改用户数据
    try:
        g.user.nick_name = nick_name
        g.user.signature = signature
        g.user.gender = gender
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="修改失败")
    #6.返回响应
    return jsonify(errno=RET.OK,errmsg="修改成功")


# 获取用户信息首页
# 请求路径: /user/info
# 请求方式:GET
# 请求参数:无
# 返回值: user.html页面,用户字典data数据
@profile_blue.route('/info')
@user_login_data
def user_info():

    #判断用户是否有登陆
    if not g.user:
        return redirect("/")

    #拼接数据,渲染页面
    data = {
        "user_info":g.user.to_dict()
    }
    return render_template("news/user.html",data=data)
