from flask import render_template, current_app, abort, jsonify, session, g, request

from info import db
from info.models import News, User, Comment, CommentLike
from info.response_code import RET
from info.utils.commons import user_login_data
from . import news_blue

# 关注与取消关注
# 请求路径: /news/followed_user
# 请求方式: POST
# 请求参数:user_id,action
# 返回值: errno, errmsg
@news_blue.route('/followed_user', methods=['POST'])
@user_login_data
def followed_user():
    """
    - 1.判断用户是否有登陆
    - 2.获取参数
    - 3.校验参数,为空校验
    - 4.操作类型校验
    - 5.根据作者编号取出作者对象,判断作者对象是否存在
    - 6.根据操作类型,关注&取关
    - 7.返回响应
    :return:
    """
    # - 1.判断用户是否有登陆
    if not g.user:
        return jsonify(errno=RET.NODATA,errmsg="用户未登录")

    # - 2.获取参数
    author_id = request.json.get("user_id")
    action = request.json.get("action")

    # - 3.校验参数,为空校验
    if not all([author_id,action]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不全")

    # - 4.操作类型校验
    if not action in ["follow","unfollow"]:
        return jsonify(errno=RET.DATAERR,errmsg="操作类型有误")

    # - 5.根据作者编号取出作者对象,判断作者对象是否存在
    try:
        author = User.query.get(author_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取作者异常")

    # - 6.根据操作类型,关注&取关
    try:
        if action == "follow":
            #判断是否关注过作者
            if not g.user in author.followers:
                author.followers.append(g.user)
        else:
            #判断是否关注过作者
            if g.user in author.followers:
                author.followers.remove(g.user)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="操作失败")

    # - 7.返回响应
    return jsonify(errno=RET.OK,errmsg="操作成功")



# 评论点赞
# 请求路径: /news/comment_like
# 请求方式: POST
# 请求参数:news_id,comment_id,action,g.user
# 返回值: errno,errmsg
@news_blue.route('/comment_like', methods=['POST'])
@user_login_data
def comment_like():
    """
    - 1.判断用户是否登陆
    - 2.获取参数
    - 3.校验参数,为空校验
    - 4.判断操作类型
    - 5.根据评论编号取出评论对象,判断评论是否存在
    - 6.根据操作类型,点赞或者取消点赞
    - 7.返回响应
    :return:
    """
    # - 1.判断用户是否登陆
    if not g.user:
        return jsonify(errno=RET.NODATA,errmsg="用户未登录")

    # - 2.获取参数
    comment_id = request.json.get("comment_id")
    action = request.json.get("action")

    # - 3.校验参数,为空校验
    if not all([comment_id,action]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不全")

    # - 4.判断操作类型
    if not action in ["add","remove"]:
        return jsonify(errno=RET.DATAERR,errmsg="操作类型有误")

    # - 5.根据评论编号取出评论对象,判断评论是否存在
    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取评论失败")

    if not comment: return jsonify(errno=RET.NODATA,errmsg="评论不存在")

    # - 6.根据操作类型,点赞或者取消点赞
    try:
        if action == "add":
            #判断用户是否有点过赞
            comment_like = CommentLike.query.filter(CommentLike.comment_id == comment_id,CommentLike.user_id == g.user.id).first()
            if not comment_like:
                #创建点赞对象,设置属性
                comment_like = CommentLike()
                comment_like.comment_id = comment_id
                comment_like.user_id = g.user.id
    
                #添加到数据库
                db.session.add(comment_like)
                db.session.commit()
    
                #将评论的点赞数量+1
                comment.like_count += 1
        else:
            #判断用户是否有点过赞
            comment_like = CommentLike.query.filter(CommentLike.comment_id == comment_id,CommentLike.user_id == g.user.id).first()
            if  comment_like:
                #删除点赞对象
                db.session.delete(comment_like)
    
                #添加到数据库
                db.session.commit()
    
                #将评论的点赞数量-1
                if comment.like_count > 0:
                    comment.like_count -= 1
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg="操作失败")

    # - 7.返回响应
    return jsonify(errno=RET.OK,errmsg="操作成功")


# 新闻评论后端
# 请求路径: /news/news_comment
# 请求方式: POST
# 请求参数:news_id,comment,parent_id, g.user
# 返回值: errno,errmsg,评论字典
@news_blue.route('/news_comment', methods=['POST'])
@user_login_data
def news_comment():
    """
    - 1.判断用户是否登陆
    - 2.获取参数
    - 3.校验参数,为空校验
    - 4.根据新闻编号取出新闻对象,并判断新闻是否存在
    - 5.创建评论对象,设置属性
    - 6.添加评论到数据库
    - 7.返回响应
    :return:
    """
    # - 1.判断用户是否登陆
    if not g.user:
        return jsonify(errno=RET.NODATA,errmsg="用户未登录")
    
    # - 2.获取参数
    news_id = request.json.get("news_id")
    content = request.json.get("comment")
    parent_id = request.json.get("parent_id")
    
    # - 3.校验参数,为空校验
    if not all([news_id,content]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不全")
    
    # - 4.根据新闻编号取出新闻对象,并判断新闻是否存在
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="新闻获取失败")
    
    if not news: return jsonify(errno=RET.NODATA,errmsg="新闻不存在")
    
    # - 5.创建评论对象,设置属性
    comment =  Comment()
    comment.user_id = g.user.id
    comment.news_id = news_id
    comment.content = content
    
    #判断是否有父评论
    if parent_id:
        comment.parent_id = parent_id
    
    # - 6.添加评论到数据库
    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg="评论失败")
    
    # - 7.返回响应
    return jsonify(errno=RET.OK,errmsg="评论成功",data=comment.to_dict())


# 收藏功能接口
# 请求路径: /news/news_collect
# 请求方式: POST
# 请求参数:news_id,action, g.user
# 返回值: errno,errmsg
@news_blue.route('/news_collect',methods=["POST"])
@user_login_data
def news_collect():
    """
    - 0.判断用户是否登陆
    - 1.获取参数
    - 2.校验参数,为空检验
    - 3.判断操作类型
    - 4.根据新闻编号取出新闻对象,判断新闻对象是否存在
    - 5.根据操作类型,收藏&取消收藏新闻
    - 6.返回响应
    :return:
    """
    # - 0.判断用户是否登陆
    if not g.user:
        return jsonify(errno=RET.NODATA,errmsg="用户未登录")

    # - 1.获取参数
    news_id = request.json.get("news_id")
    action = request.json.get("action")

    # - 2.校验参数,为空检验
    if not all([news_id,action]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不全")

    # - 3.判断操作类型
    if not action in ['collect',"cancel_collect"]:
        return jsonify(errno=RET.DATAERR,errmsg="操作类型有误")

    # - 4.根据新闻编号取出新闻对象,判断新闻对象是否存在
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="新闻获取失败")

    if not news:
        return jsonify(errno=RET.NODATA,errmsg="新闻不存在")

    # - 5.根据操作类型,收藏&取消收藏新闻
    try:
        if action == "collect":
            #判断用户是否已经收藏过新闻了
            if not news in g.user.collection_news:
                g.user.collection_news.append(news)
        else:
            #判断用户是否已经收藏过新闻了
            if  news in g.user.collection_news:
                g.user.collection_news.remove(news)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="操作失败")

    # - 6.返回响应
    return jsonify(errno=RET.OK,errmsg="操作成功")


# 新闻详情展示(用户)
# 请求路径: /news/<int:news_id>
# 请求方式: GET
# 请求参数:news_id
# 返回值: detail.html页面, 用户data字典数据
@news_blue.route('/<int:news_id>')
@user_login_data
def news_detail(news_id):

    #根据新闻编号查询新闻对象
    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)

    #判断新闻对象是否存在
    if not news:
        abort(404)

    #查询前6条热门新闻
    try:
        click_news = News.query.order_by(News.clicks.desc()).limit(6).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取新闻失败")

    #将新闻对象列表,转成字典列表
    click_news_list = []
    for item in click_news:
        click_news_list.append(item.to_dict())

    #判断用户是否有收藏过该新闻
    is_collected = False
    if g.user and news in g.user.collection_news:
        is_collected = True

    #查询所有的评论对象
    try:
        comments = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取评论失败")

    #找出用户所有点过的赞
    commentlikes = []
    try:
        if g.user:
            commentlikes = CommentLike.query.filter(CommentLike.user_id == g.user.id).all()
    except Exception as e:
        current_app.logger.error(e)

    # 获取用户点赞过的评论编号列表
    comment_like_ids = []
    for commentlike in commentlikes:
        comment_like_ids.append(commentlike.comment_id)

    #将评论对象列表转成字典列表
    comment_list = []
    for comment in comments:

        comm_dict = comment.to_dict()
        #设置点赞key
        comm_dict["is_like"] = False

        #判断用户是否是否对该评论点过赞
        # if 用户需要登陆 and 判断当前的评论是否,在用户点赞过的评论编号列表里面
        if g.user and comment.id in comment_like_ids:
            comm_dict["is_like"] = True

        comment_list.append(comm_dict)


    #判断当前登录的用户,是否有关注该新闻的作者
    is_followed = False
    if g.user and news.user: #用户登陆了, 并且新闻有作者
        if g.user in news.user.followers: #登陆的用户,在作者的粉丝列表中
            is_followed = True

    #拼接数据渲染页面
    data = {
        "news_info":news.to_dict(),
        "click_news_list":click_news_list,
        "user_info": g.user.to_dict() if g.user else "",
        "is_collected":is_collected,
        "comments":comment_list,
        "is_followed":is_followed
    }
    return render_template("news/detail.html",data=data)
