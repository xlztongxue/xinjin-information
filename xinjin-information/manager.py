import datetime
import logging
import random

from flask_migrate import Migrate,MigrateCommand
from flask_script import Manager
from flask import Flask,session,current_app
from info import create_app,db,models #导入models让程序知道有这个文件的存在

#获取app应用程序对象,
from info.models import User

app = create_app("develop")

#1.创建Migrate对象,关联app,db
Migrate(app,db)

#2.创建Manager对象,关联
manager = Manager(app)

#3.给manger添加操作命令
manager.add_command("db",MigrateCommand)

#创建管理员函数
#参数1:调用方法的时候传递的参数名  参数2: 对前面参数的解释  参数3: 目标参数,用来传递函数的形式参数的
@manager.option('-p', '--password', dest='password')
@manager.option('-u', '--username', dest='username')
def create_superuser(password,username):
    #1.创建管理员对象
    admin = User()

    #2.设置属性
    admin.nick_name = username
    admin.password = password
    admin.mobile = username
    admin.is_admin = True

    #3.添加到数据库
    try:
        db.session.add(admin)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return "创建失败"

    return "创建成功"

#为了方便查看图表,添加测试用户
@manager.option('-t', '--test', dest='test')
def add_test_user(test):
    #1.定义容器
    user_list = []

    #2.for循环创建用户,并添加到容器
    for i in range(0,1000):
        user = User()
        user.mobile = "138%08d"%i
        user.nick_name = "老王%d"%i
        user.password_hash = "pbkdf2:sha256:50000$Nu9CqLOK$036d68c31706e7358e924ff739ea3bba288a2de89ecab119d0c29ab9dcb9ba30"
        #设置,近31天以来,最后一次登陆时间
        user.last_login = datetime.datetime.now() - datetime.timedelta(seconds=random.randint(0,3600*24*31))

        user_list.append(user)

    #3.保存用户到数据库
    try:
        db.session.add_all(user_list)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return "创建失败"

    return "创建成功"


if __name__ == '__main__':
    manager.run()