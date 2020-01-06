from flask import Blueprint

#创建认证蓝图对象
passport_blue = Blueprint("passport",__name__,url_prefix="/passport")

#装饰视图函数
from . import views