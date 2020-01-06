#### 项目介绍
这是一个新闻类型的网站

### 部署

* 创建数据库

  ```
  create database info19 charset=utf8;
  ```

* 创建虚拟环境

  ```shell
  mkvirtualenv -p python3 info19
  cd /home/python/information19
  pip install -r requirements.txt
  ```

* 迁移数据库-使用模型类生成表

  ```shell
  # 初始化
  python manager.py db init
  # 生成迁移脚本
  python manager.py db migrate
  # 执行迁移脚本
  python manager.py db upgrade
  ```

* 导入测试数据

  ```mysql
  mysql -uroot -p
  use info19;
  # 导入新闻分类
  source /home/python/information19/mysql_db/information_info_category.sql
  # 导入新闻数据
  source /home/python/information19/mysql_db/information_info_news.sql
  ```

* 运行代码

  ```
  python manager.py runserver -h 172.16.86.172
  ```

* 创建管理员

  ```
  python manager.py create_superuser -u laowang -p 123456
  ```

* 查看所有路由

  ```
  http://172.16.86.172:5000/all_route
  ```

* 登录后台管理

  ```
  http://172.16.86.172:5000/admin/login
  ```

* 普通用户注册-登录

  ```
  http://172.16.86.170:5000/
  验证码答应在控制台中
  ```

* 测试发布新闻流程

  ```
  1.管理员添加分类
  2.普通用户发布文章在此分类下
  3.管理员审核文章
  4.在首页看分类新闻
  ```

  

  

