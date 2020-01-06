from info import redis_store, constants
from info.models import User, News, Category
from info.response_code import RET
from info.utils.commons import user_login_data
from . import index_blue
from flask import render_template, current_app, session, jsonify, request, g


# 首页新闻列表获取
# 请求路径: /newslist
# 请求方式: GET
# 请求参数: cid,page,per_page
# 返回值: data数据
@index_blue.route('/newslist')
@user_login_data
def newslist():
    """
    - 1.获取参数
    - 2.参数类型转换
    - 3.分页查询
    - 4.获取分页对象属性,总页数,当前页,当前页对象列表
    - 5.拼接数据,返回响应
    :return:
    """
    # - 1.获取参数
    cid = request.args.get("cid","1")
    page = request.args.get("page","1")
    per_page = request.args.get("per_page","10")

    # - 2.参数类型转换
    try:
        page = int(page)
        per_page = int(per_page)
    except Exception as e:
        page = 1
        per_page = 10

    # - 3.分页查询
    try:

        #判断分类编号是否不等于1
        filter_condition = [News.status == 0]
        if cid != "1":
            filter_condition.append(News.category_id == cid)

        paginate = News.query.filter(*filter_condition).order_by(News.create_time.desc()).paginate(page,per_page,False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取新闻失败")

    # - 4.获取分页对象属性,总页数,当前页,当前页对象列表
    totalPage = paginate.pages
    currentPage = paginate.page
    items = paginate.items

    #5. 对象列表转成字典列表
    news_list = []
    for item in items:
        news_list.append(item.to_dict())

    # - 6.拼接数据,返回响应
    return jsonify(errno=RET.OK,errmsg="获取成功",totalPage=totalPage,currentPage=currentPage,newsList=news_list)


@index_blue.route('/',methods=["GET","POST"])
@user_login_data
def show_index():

    # #1.取出session中用户的编号
    # user_id = session.get("user_id")
    #
    # #2.根据user_id取出用户对象
    # user = None
    # if user_id:
    #     try:
    #         user = User.query.get(user_id)
    #     except Exception as e:
    #         current_app.logger.error(e)

    #2.1 查询热门新闻,前10条,按照点击量排序
    try:
        news = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="查询新闻失败")

    #2.2 将对象列表,转成字典列表
    click_news_list = []
    for item in news:
        click_news_list.append(item.to_dict())

    #2.3 查询所有分类信息
    try:
        categories = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取分类失败")

    #2.4将分类对象列表,转成字典列表
    category_list = []
    for category in categories:
        category_list.append(category.to_dict())


    #3.携带用户数据,渲染页面
    data = {
        #如果user不为空,返回左侧的值作为结果,否则返回右侧空字符串
        "user_info":g.user.to_dict() if g.user else "",
        "click_news_list":click_news_list,
        "categories":category_list
    }
    return render_template("news/index.html",data=data)


#处理网站logo
"""
所有网站都有logo,浏览器会自动发送一个get请求,地址是/favicon.ico
- 目的: 获取服务器提供的logo图标
加载static中的静态文件方法:
current_app.send_static_file('文件名A'), 自动加载static文件夹中的文件A,并生成一个响应体对象
"""
@index_blue.route('/favicon.ico')
def get_web_logo():
    return current_app.send_static_file("news/favicon.ico")