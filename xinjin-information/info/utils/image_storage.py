from qiniu import Auth, put_file, etag,put_data
import qiniu.config
#需要填写你的 Access Key 和 Secret Key
access_key = '51DGWfSzbBws6szT3GVoZ8nMuqVVFAFV2P_StMbr'
secret_key = 'pAo3kBotA7PQLCuIF9Y2wCc7AfRs0MEss2-qdTbb'

def image_storage(image_data):
    #构建鉴权对象
    q = Auth(access_key, secret_key)

    #要上传的空间
    bucket_name = 'toutiao-cspy6'

    #上传到七牛后保存的文件名,如果不指定,名字由七牛云维护
    # key = 'my-python-logo.png'
    key = None

    #生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, key, 3600)

    #要上传文件的本地路径
    # localfile = './11.jpg'

    # ret, info = put_file(token, key, localfile)
    ret, info = put_data(token, key, image_data)
    print(info)

    #如果上传成功,返回图片名字,否则返回空
    if info.status_code == 200:
        return ret.get("key")
    else:
        return ""


#测试
if __name__ == '__main__':
    #1. 测试上传文件,使用with,会自动关闭io流
    with open('./11.jpg','rb') as f:
        image_name = image_storage(f.read())
        print(image_name)
