from flask import Blueprint

#创建蓝图对象
profile_blue = Blueprint("profile",__name__,url_prefix="/user")

#装饰视图函数
from . import views