from flask import Blueprint, request, session, redirect

#创建管理员蓝图对象
admin_blue = Blueprint("admin",__name__,url_prefix="/admin")

#装饰视图函数
from . import views


#使用请求钩子,两个作用
#1. 拦截访问admin_blue装饰的非登陆的,视图函数
#2. 如果是普通用户拦截, 如果是管理员不拦截
@admin_blue.before_request
def before_request():
    #1.判断访问的是否是登陆页面
    # if request.url.endswith("/admin/login"):
    #     pass
    # else:
    #     #2.判断是否访问了其他页面
    #     if session.get("is_admin"):
    #         pass
    #     else:
    #         return redirect("/")


    #将上面的代码优化
    if not request.url.endswith("/admin/login"):
        if not session.get("is_admin"):
            return redirect("/")
