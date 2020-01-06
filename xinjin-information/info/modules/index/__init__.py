from flask import Blueprint

#创建首页蓝图对象
index_blue = Blueprint("index",__name__)

#装饰视图函数
from . import views