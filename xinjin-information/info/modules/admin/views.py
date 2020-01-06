import datetime
from  datetime import timedelta

from flask import render_template, request, session, redirect, g, current_app, jsonify
import time
from info import user_login_data, constants, db
from info.models import User, News, Category
from info.response_code import RET
from info.utils.image_storage import image_storage
from . import admin_blue

# 新闻分类添加/修改
# 请求路径: /admin/add_category
# 请求方式: POST
# 请求参数: id,name
# 返回值:errno,errmsg
@admin_blue.route('/add_category', methods=['POST'])
def add_category():
    #1.获取参数
    category_id = request.json.get("id")
    category_name = request.json.get("name")

    #2.校验参数
    if not category_name:
        return jsonify(errno=RET.PARAMERR,errmsg="参数不全")

    #3.根据分类编号判断,是做增加,还是编辑操作
    if category_id:

        #3.1根据分类编号查询分类对象,判断是否存在
        try:
            category = Category.query.get(category_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR,errmsg="获取分类失败")

        if not category: return jsonify(errno=RET.DBERR,errmsg="分类不存在")

        #3.2修改分类名字
        category.name = category_name

    else:
        #3.3创建分类对象
        category = Category()

        #3.4设置属性保存到数据库
        category.name = category_name
        try:
            db.session.add(category)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=RET.DBERR,errmsg="添加分类失败")

    #4.返回响应
    return jsonify(errno=RET.OK,errmsg="操作成功")


# 新闻分类管理
# 请求路径: /admin/news_category
# 请求方式: GET
# 请求参数: GET,无
# 返回值:GET,渲染news_type.html页面, data数据
@admin_blue.route('/news_category')
def news_category():
    #1.查询所有分类
    try:
        categories = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return render_template("admin/news_type.html",errmsg="获取分类失败")

    #2.拼接数据渲染页面
    return render_template("admin/news_type.html",categories=categories)


# 获取/设置新闻版式编辑详情
# 请求路径: /admin/news_edit_detail
# 请求方式: GET, POST
# 请求参数: GET, news_id, POST(news_id,title,digest,content,index_image,category_id)
# 返回值:GET,渲染news_edit_detail.html页面,data字典数据, POST(errno,errmsg)
@admin_blue.route('/news_edit_detail', methods=['GET', 'POST'])
def news_edit_detail():
    """
     - 1.判断请求方式
     - 2.如果是get,根据新闻编号获取新闻对象,判断是否存在
     - 3.携带新闻数据,渲染页面
     - 4.获取参数
     - 5.校验操作,为空校验,操作类型校验
     - 6.根据新闻编号查询新闻对象,判断是否存在
     - 7.根据操作类型,改变新闻的状态
     - 8.返回响应
     :return:
     """
    # - 1.判断请求方式
    if request.method == "GET":
        # - 2.如果是get,根据新闻编号获取新闻对象,判断是否存在
        news_id = request.args.get("news_id")
        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)
            return render_template("admin/news_review_detail.html", errmsg="获取新闻失败")

        if not news: return render_template("admin/news_review_detail.html", errmsg="新闻不存在")

        #2.1查询所有分类
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return render_template("admin/news_review_detail.html", errmsg="获取分类失败")

        # - 3.携带新闻数据,渲染页面
        return render_template("admin/news_edit_detail.html", news=news.to_dict(),categories=categories)

    # - 4.获取参数,news_id,title,digest,content,index_image,category_id
    news_id = request.form.get("news_id")
    title = request.form.get("title")
    digest = request.form.get("digest")
    content = request.form.get("content")
    index_image = request.files.get("index_image")
    category_id = request.form.get("category_id")


    # - 5.校验操作,为空校验,操作类型校验
    if not all([news_id, title,digest,content,index_image,category_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不全")

    # - 6.根据新闻编号查询新闻对象,判断是否存在
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return render_template("admin/news_review_detail.html", errmsg="获取新闻失败")

    if not news: return render_template("admin/news_review_detail.html", errmsg="新闻不存在")

    # - 7.上传图片,判断图片是否上传成功
    try:
        image_name = image_storage(index_image.read())
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg="七牛云异常")

    if not image_name:return jsonify(errno=RET.NODATA,errmsg="图片上传失败")

    #8.修改新闻对象属性
    try:
        news.title = title
        news.digest = digest
        news.content = content
        news.index_image_url = constants.QINIU_DOMIN_PREFIX + image_name
        news.category_id = category_id
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="编辑失败")

    #9.返回响应
    return jsonify(errno=RET.OK,errmsg="编辑成功")



# 新闻版式编辑
# 请求路径: /admin/news_edit
# 请求方式: GET
# 请求参数: GET, p, keywords
# 返回值:GET,渲染news_edit.html页面,data字典数据
@admin_blue.route('/news_edit')
def news_edit():
    """
    - 1.获取参数
    - 2.参数类型转换
    - 3.分页查询新闻对象
    - 4.获取分页对象属性,总页数,当前页,当前页新闻列表
    - 5.新闻对象列表转成字典列表
    - 6.拼接数据,渲染页面
    :return:
    """
    # - 1.获取参数
    page = request.args.get("p","1")
    keywords = request.args.get("keywords")

    # - 2.参数类型转换
    try:
        page = int(page)
    except Exception as e:
        page = 1

    # - 3.分页查询新闻对象
    try:

        query_condition = []
        #判断是否有搜索关键字
        if keywords:
            query_condition.append(News.title.contains(keywords))

        paginate = News.query.filter(*query_condition).order_by(News.create_time.desc()).paginate(page,10,False)
    except Exception as e:
        current_app.logger.error(e)
        return render_template("admin/news_edit.html",errmsg="获取新闻失败")

    # - 4.获取分页对象属性,总页数,当前页,当前页新闻列表
    totalPage = paginate.pages
    currentPage = paginate.page
    items = paginate.items

    # - 5.新闻对象列表转成字典列表
    news_list = []
    for item in items:
        news_list.append(item.to_review_dict())

    # - 6.拼接数据,渲染页面
    data = {
        "totalPage":totalPage,
        "currentPage":currentPage,
        "news":news_list
    }
    return render_template("admin/news_edit.html", data=data)


# 获取/设置新闻审核详情
# 请求路径: /admin/news_review_detail
# 请求方式: GET,POST
# 请求参数: GET, news_id, POST,news_id, action
# 返回值:GET,渲染news_review_detail.html页面,data字典数据
@admin_blue.route('/news_review_detail', methods=['GET', 'POST'])
def news_review_detail():
    """
    - 1.判断请求方式
    - 2.如果是get,根据新闻编号获取新闻对象,判断是否存在
    - 3.携带新闻数据,渲染页面
    - 4.获取参数
    - 5.校验操作,为空校验,操作类型校验
    - 6.根据新闻编号查询新闻对象,判断是否存在
    - 7.根据操作类型,改变新闻的状态
    - 8.返回响应
    :return:
    """
    # - 1.判断请求方式
    if request.method == "GET":
        # - 2.如果是get,根据新闻编号获取新闻对象,判断是否存在
        news_id = request.args.get("news_id")
        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)
            return render_template("admin/news_review_detail.html",errmsg="获取新闻失败")

        if not news: return render_template("admin/news_review_detail.html",errmsg="新闻不存在")

        # - 3.携带新闻数据,渲染页面
        return render_template("admin/news_review_detail.html",news=news.to_dict())

    # - 4.获取参数
    news_id = request.json.get("news_id")
    action = request.json.get("action")

    # - 5.校验操作,为空校验,操作类型校验
    if not all([news_id,action]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不全")

    if not action in ["accept","reject"]:
        return jsonify(errno=RET.DATAERR,errmsg="操作类型有误")

    # - 6.根据新闻编号查询新闻对象,判断是否存在
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return render_template("admin/news_review_detail.html", errmsg="获取新闻失败")

    if not news: return render_template("admin/news_review_detail.html", errmsg="新闻不存在")

    # - 7.根据操作类型,改变新闻的状态
    try:
        if action == "accept":
            news.status = 0
        else:
            news.status = -1
            news.reason = request.json.get("reason", "")
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="操作失败")

    # - 8.返回响应
    return jsonify(errno=RET.OK, errmsg="操作成功")



# 获取/设置新闻审核
# 请求路径: /admin/news_review
# 请求方式: GET
# 请求参数: GET, p,keywords
# 返回值:渲染user_list.html页面,data字典数据
@admin_blue.route('/news_review')
def news_review():
    """
    - 1.获取参数
    - 2.参数类型转换
    - 3.分页查询新闻对象
    - 4.获取分页对象属性,总页数,当前页,当前页新闻列表
    - 5.新闻对象列表转成字典列表
    - 6.拼接数据,渲染页面
    :return:
    """
    # - 1.获取参数
    page = request.args.get("p","1")
    keywords = request.args.get("keywords")

    # - 2.参数类型转换
    try:
        page = int(page)
    except Exception as e:
        page = 1

    # - 3.分页查询新闻对象
    try:

        query_condition = [News.status != 0]
        #判断是否有搜索关键字
        if keywords:
            query_condition.append(News.title.contains(keywords))

        paginate = News.query.filter(*query_condition).order_by(News.create_time.desc()).paginate(page,10,False)
    except Exception as e:
        current_app.logger.error(e)
        return render_template("admin/news_review.html",errmsg="获取新闻失败")

    # - 4.获取分页对象属性,总页数,当前页,当前页新闻列表
    totalPage = paginate.pages
    currentPage = paginate.page
    items = paginate.items

    # - 5.新闻对象列表转成字典列表
    news_list = []
    for item in items:
        news_list.append(item.to_review_dict())

    # - 6.拼接数据,渲染页面
    data = {
        "totalPage":totalPage,
        "currentPage":currentPage,
        "news":news_list
    }
    return render_template("admin/news_review.html", data=data)

# 用户列表
# 请求路径: /admin/user_list
# 请求方式: GET
# 请求参数: p
# 返回值:渲染user_list.html页面,data字典数据
@admin_blue.route('/user_list')
def user_list():
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

    # - 3.分页查询普通用户
    try:
        paginate = User.query.filter(User.is_admin == False).order_by(User.create_time.desc()).paginate(page,10,False)
    except Exception as e:
        current_app.logger.error(e)
        return render_template("admin/user_list.html",errmsg="获取用户失败")

    # - 4.获取分页对象属性,总页数,当前页,当前页用户列表
    totalPage = paginate.pages
    currentPage = paginate.page
    items = paginate.items

    # - 5.用户列表转成,字典列表
    user_list = []
    for item in items:
        user_list.append(item.to_admin_dict())

    # - 6.携带数据,渲染页面
    data = {
        "totalPage":totalPage,
        "currentPage":currentPage,
        "users":user_list
    }
    return render_template("admin/user_list.html",data=data)


# 用户统计
# 请求路径: /admin/user_count
# 请求方式: GET
# 请求参数: 无
# 返回值:渲染页面user_count.html,字典数据
@admin_blue.route('/user_count')
def user_count():
    """
    - 1.查询总人数(不包含管理员)
    - 2.查询月活人数
    - 3.查询日活人数
    - 4.查询活跃时间段内,登陆的人数
    - 5.携带数据,渲染页面
    :return:
    """
    # - 1.查询总人数(不包含管理员)
    try:
        total_count = User.query.filter(User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)
        return render_template("admin/user_count.html",errmsg="总人数查询失败")

    # - 2.查询月活人数
    #获取本地时间对象
    local_time = time.localtime()
    try:

        #获取本月1号0点,的字符串
        start_mon_str = "%d-%d-1"%(local_time.tm_year,local_time.tm_mon) #2018-12-1

        #将本月1号0点,的字符串转成时间对象
        start_mon_date = datetime.datetime.strptime(start_mon_str,"%Y-%m-%d")

        #从本月1号0点,到目前为止登陆的用户
        mon_count = User.query.filter(User.last_login > start_mon_date,User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)
        return render_template("admin/user_count.html",errmsg="获取月活失败")

    # - 3.查询日活人数
    try:

        #获取本日0点,的字符串
        start_day_str = "%d-%d-%d"%(local_time.tm_year,local_time.tm_mon,local_time.tm_mday) #2018-12-7

        #将本日0点,的字符串,的字符串转成时间对象
        start_day_date = datetime.datetime.strptime(start_day_str,"%Y-%m-%d")

        #从本日0点,到目前为止登陆的用户
        day_count = User.query.filter(User.last_login > start_day_date,User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)
        return render_template("admin/user_count.html",errmsg="获取日活失败")

    # - 4.查询活跃时间段内,登陆的人数
    active_date = [] #活跃时间段
    active_count = [] #活跃人数
    for i in range(0, 31):
        # 当天开始时间A
        begin_date = start_day_date - timedelta(days=i)

        # 当天开始时间, 的后⼀一天B
        end_date = start_day_date - timedelta(days=i-1)

        # 添加当天开始时间字符串串到, 活跃⽇日期中
        active_date.append(begin_date.strftime("%m-%d"))

        # 查询时间A到B这⼀一天的注册⼈人数 
        everyday_active_count = User.query.filter(User.is_admin==False,User.last_login>=begin_date,User.last_login<=end_date).count()

        # 添加当天注册⼈人数到,获取数量量中
        active_count.append(everyday_active_count)

    #为了方便查看图表,反转容器
    active_date.reverse()
    active_count.reverse()

    # - 5.携带数据,渲染页面
    data = {
        "total_count":total_count,
        "mon_count":mon_count,
        "day_count":day_count,
        "active_date":active_date,
        "active_count":active_count
    }
    return render_template("admin/user_count.html",data=data)


# 后台主页内容
# 请求路径: /admin/index
# 请求方式: GET
# 请求参数: 无
# 返回值:渲染页面index.html,user字典数据
@admin_blue.route('/index')
@user_login_data
def admin_index():

    #判断是否不是管理员
    if not session.get("is_admin"):
        return redirect("/")

    #获取用户数据,展示页面
    return render_template("admin/index.html",user_info=g.user.to_dict())



# 获取/登陆,管理员登陆
# 请求路径: /admin/login
# 请求方式: GET,POST
# 请求参数:GET,无, POST,username,password
# 返回值: GET渲染login.html页面, POST,login.html页面,errmsg
@admin_blue.route('/login',methods=["GET","POST"])
def admin_login():
    """
    - 1.判断请求方式
    - 2.获取参数
    - 3.校验参数,为空校验
    - 4.根据用户登陆名称查询管理员对象,并判断是否存在
    - 5.判断管理员密码是否正确
    - 6.记录管理员登陆信息到session
    - 7.返回首页重定向
    :return:
    """
    # - 1.判断请求方式
    if request.method == "GET":

        #判断管理员是否登陆过
        if session.get("is_admin"):
            return redirect("/admin/index")

        return render_template("admin/login.html")

    # - 2.获取参数
    username = request.form.get("username")
    password = request.form.get("password")

    # - 3.校验参数,为空校验
    if not all([username,password]):
        return render_template("admin/login.html",errmsg="参数不全")

    # - 4.根据用户登陆名称查询管理员对象,并判断是否存在
    try:
        admin = User.query.filter(User.mobile == username,User.is_admin == True).first()
    except Exception as e:
        return render_template("admin/login.html", errmsg="管理员获取失败")

    if not admin: return render_template("admin/login.html",errmsg="管理员不存在")

    # - 5.判断管理员密码是否正确
    if not admin.check_password(password):
        return render_template("admin/login.html",errmsg="密码不正确")

    # - 6.记录管理员登陆信息到session
    session["user_id"] = admin.id
    session["nick_name"] = admin.nick_name
    session["mobile"] = admin.mobile
    session["is_admin"] = True

    # - 7.返回首页重定向
    # return redirect("https://www.taobao.com")
    return redirect("/admin/index")
