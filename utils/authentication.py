import jwt
import time
from math import floor
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from like import models
from drf import settings

def time_format(timestamp):
    timeArray = time.localtime(timestamp)
    otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    return otherStyleTime

class headerPostAuthentication(BaseAuthentication):
    def authenticate(self, request):
        if request.method=='POST':
            try:
                token = request.headers['Authorization']
            except:  # 如果没有Authorization字段
                raise AuthenticationFailed({"code": 104, "msg": "用户未登录"})

            if not token:  # 如果token==‘’
                raise AuthenticationFailed({"code":104,"msg":"用户未登录"})
            try:
                info = jwt.decode(jwt=token, key=settings.SECRET_KEY,verify=True,  algorithms='HS256')
                if info['iat'] > floor(time.time()):
                    raise AuthenticationFailed({"code":105,"msg":"token发行时间大于现在时间"})
            except:
                raise AuthenticationFailed({"code":102,"msg":"token验证失败"})
            user_object = models.User.objects.filter(account=info['sub']).first()
            if user_object:
                if user_object.identity == 'c' :
                    raise AuthenticationFailed({"code":106,"msg":"您已被封禁"})
                elif user_object.identity == 'b':
                    if user_object.banned.timestamp()>floor(time.time()):
                        raise AuthenticationFailed({"code":106,"msg":f'您被暂时禁言，将会在{user_object.banned}解禁'})
                    else:
                        user_object.identity = 'v'
                        user_object.save()
                if floor(time.time())-info['iat'] > 30000:  # 检测jwt是否过期
                    raise AuthenticationFailed({"code":101,"msg":"token已过期，请重新登录"})
                return user_object,token
            else:
                raise AuthenticationFailed({"code":103,"msg":"用户不存在"})
    def authenticate_header(self, request):
        return "API"

class headerDeleteAuthentication(BaseAuthentication):
    def authenticate(self, request):
        if request.method=='DELETE':
            try:
                token = request.headers['Authorization']
            except:  # 如果没有Authorization字段
                raise AuthenticationFailed({"code": 104, "msg": "用户未登录"})

            if not token:  # 如果token==‘’
                raise AuthenticationFailed({"code":104,"msg":"用户未登录"})
            try:
                info = jwt.decode(jwt=token, key=settings.SECRET_KEY,verify=True,  algorithms='HS256')
                if info['iat'] > floor(time()):
                    raise AuthenticationFailed({"code":105,"msg":"token发行时间大于现在时间"})
            except:
                raise AuthenticationFailed({"code":102,"msg":"token验证失败"})
            user_object = models.User.objects.filter(account=info['sub']).first()
            if user_object:
                if user_object.identity == 'c' :
                    raise AuthenticationFailed({"code":106,"msg":"您已被封禁"})
                elif user_object.identity == 'b':
                    if user_object.banned>floor(time()):
                        raise AuthenticationFailed({"code":106,"msg":f'您被暂时禁言，将会在{time_format(user_object.banned)}解禁'})
                    else:
                        user_object.identity = 'v'
                        user_object.save()
                if floor(time())-info['iat'] > 30000:  # 检测jwt是否过期
                    raise AuthenticationFailed({"code":101,"msg":"token已过期，请重新登录"})
                return user_object,token
            else:
                raise AuthenticationFailed({"code":103,"msg":"用户不存在"})
    def authenticate_header(self, request):
        return "API"