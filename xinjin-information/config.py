import logging
from datetime import timedelta
from redis import StrictRedis
#设置配置类
class Config(object):

    #设置调试模式
    DEBUG = True
    SECRET_KEY = "fdjkfjkdf"

    #数据库配置
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:mysql@localhost:3306/info19"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True #当视图函数结束的时候,自动提交一次会话
    SQLALCHEMY_ECHO = False

    #redis配置信息
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    #session配置信息
    SESSION_TYPE = "redis" #存储类型
    SESSION_REDIS = StrictRedis(host=REDIS_HOST,port=REDIS_PORT)
    SESSION_USE_SIGNER = True #签名存储
    PERMANENT_SESSION_LIFETIME = timedelta(seconds=3600*24*2) #两天有效

    #默认日志级别就是DEBUG
    LEVELNAME = logging.DEBUG

#开发模式配置信息
class DevelopConfig(Config):
    pass

#生产(线上)模式配置信息
class ProductConfig(Config):
    DEBUG = False
    LEVELNAME = logging.ERROR

#测试模式配置信息
class TestingConfig(Config):
    TESTING = True


#提供配置类的统一访问入口
config_dict = {
    "develop":DevelopConfig,
    "product":ProductConfig,
    "testing":TestingConfig
}