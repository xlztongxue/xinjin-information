import logging
from logging.handlers import RotatingFileHandler

from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_wtf.csrf import CSRFProtect,generate_csrf
from config import config_dict
from flask import Flask, render_template, g, jsonify

#定义redis_store变量
from info.utils.commons import user_login_data

redis_store = None

#创建SQLAlchem对象
db = SQLAlchemy()

#定义create_app方法
def create_app(config_name):

    app = Flask(__name__)

    #根据配置名称,加载配置类
    config = config_dict.get(config_name)


    #调用记录日志方法
    log_file(config.LEVELNAME)

    # 加载配置类到app
    app.config.from_object(config)

    # 创建SQLAlchemy对象关联app
    # db = SQLAlchemy()
    db.init_app(app)
    #上面两句话等于 db = SQLAlchemy(app)

    # 创建redis对象
    global redis_store
    redis_store = StrictRedis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)

    # 读取app身上session配置信息
    Session(app)

    # 保护应用程序app
    CSRFProtect(app)

    # 注册首页蓝图,index_blue到app中
    from info.modules.index import index_blue
    app.register_blueprint(index_blue)

    # 注册认证蓝图,passport_blue到app中
    from info.modules.passport import passport_blue
    app.register_blueprint(passport_blue)

    # 注册新闻蓝图,news_blue到app中
    from info.modules.news import news_blue
    app.register_blueprint(news_blue)

    # 注册用户蓝图,profile_blue到app中
    from info.modules.profile import profile_blue
    app.register_blueprint(profile_blue)

    # 注册管理员蓝图,admin_blue到app中
    from info.modules.admin import admin_blue
    app.register_blueprint(admin_blue)

    # 将函数,添加到过滤器列表中
    from info.utils.commons import index_class
    app.add_template_filter(index_class,"index_class")

    #加上请求钩子,拦截所有请求,对请求数据设置csrf_token统一返回
    @app.after_request
    def after_request(resp):
        #设置csrf_token
        csrf_token = generate_csrf()
        resp.set_cookie("csrf_token",csrf_token)
        return resp


    #监听404异常的产生,返回一个完整的错误页面
    @app.errorhandler(404)
    @user_login_data
    def page_not_found(e):
        data=  {
            "user_info":g.user.to_dict() if g.user else ""
        }
        return render_template("news/404.html",data=data)


    @app.route('/all_route')
    def all_route():
        # 返回所有路由
        data = {}
        for i in app.url_map.iter_rules():
            data[i.endpoint] = i.rule
        return jsonify(data)

    # print(app.url_map)
    return app


#记录日志信息方法
def log_file(levelname):
    # 设置日志的记录等级,设置日志的等级信息,大小关系如下: DEBUG < INFO < WARING < ERROR
    logging.basicConfig(level=levelname)  # 调试debug级
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)