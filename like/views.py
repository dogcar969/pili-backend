# 框架引入
from rest_framework import views
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse,StreamingHttpResponse
from django.core.paginator import Paginator
from wsgiref.util import FileWrapper
from rest_framework.pagination import PageNumberPagination
# 其他包
from math import floor,ceil
from time import time
import datetime
from django.utils import timezone
import jwt
import json
import fasttext
import thulac
import os
# 项目内部引入
from drf import settings
from like.models import Video,User,Comment,BulletChat,BannedWord,ReportRecord,WordFrequency
from like.serializers import LikeSerializer,CommentListSerializer,CommentSendSerializer,BulletChatListSerializer,\
    BulletChatSendSerializer,VideoSerializer,BannedWordSerializer,ReportRecordSerializer,ReportRecordGetSerializer,\
BannedWordPostSerializer,WordFrequencySerializer,UserSerializer,RegisterSerializer,WordFrequencyGetSerializer
from utils.authentication import headerPostAuthentication,headerDeleteAuthentication
# 全局变量引入
DFATree = settings.GLOBAL_VARIABLES['DFATree']
safeWords = settings.GLOBAL_VARIABLES['safeWords']
trainSentences = []
trainFalseSentences = []
ft = fasttext.load_model('./fastText.bin')
thu = thulac.thulac(seg_only=True)
checkDFATree = DFATree["check"]
maskDFATree = DFATree['mask']
bannedDFATree = DFATree['banned']

noTypeError = IndexError("没有对应的分类树")

def DFATreeType(type):
    if type=='b':
        return bannedDFATree
    elif type == 'm':
        return maskDFATree
    elif type == 'c':
        return checkDFATree
    else:
        raise noTypeError

# 常量定义
DEFAULT_PAGE_NUM = 3
MAX_PAGE_SIZE = 13
# 分页器
class MyPageNumberPagination(PageNumberPagination):
    page_size = DEFAULT_PAGE_NUM  # 每页显示条数
    page_query_param = 'page'  # 查询参数
    page_size_query_param = 'pageNum'
    max_page_size = MAX_PAGE_SIZE  # 最大每页显示条数

# videoId
@api_view(['get'])
def stream_video(request):
    videoName = request.GET.get('videoName')
    def serve_video_chunk():
        # 从视频文件中读取数据块并发送给浏览器
        with open(f'media/videos/{videoName}', 'rb') as f:
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                yield chunk

    response = StreamingHttpResponse(serve_video_chunk(), content_type='video/mp4')
    response['Content-Length'] = os.path.getsize(f'media/videos/{videoName}')
    return response


class UserView(views.APIView):
    def get(self,request):
        try:
            user = User.objects.get(account=request.GET.get("account"))
            s = UserSerializer(instance=user)
            return Response(s.data,status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'msg':'无该用户'},status=status.HTTP_404_NOT_FOUND)


class VideoLikeView(views.APIView):
    # 处理视频点赞功能
    def get(self,request):
        # 获取单个点赞信息
        video = Video.objects.get(id=request.GET.get("videoId"))  # 从request获取视频id
        if video.users.filter(account=request.GET.get('userId')):  # 从数据库的点赞表里找到userId的对应视频id的点赞记录
            return Response(data={'like': 'True'}, status=status.HTTP_200_OK)
        else:
            return Response(data={"like": "False"}, status=status.HTTP_200_OK)

    def post(self,request):
        # 点赞
        UserId=request.data.get('userId')  # 从request获取视频id，用户id
        VideoId = request.data.get('videoId')
        user = User.objects.get(account=UserId)  # 获取用户对象
        video = Video.objects.get(id=VideoId)  # 获取视频对象
        video.users.add(user)  # 在点赞表里添加记录
        video.likeCount = video.likeCount+1  # 视频点赞数+1
        video.save()  # 保存修改的视频对象
        return Response(data={'like_count':video.likeCount}, status=status.HTTP_200_OK)  # 返回点赞信息

    def delete(self,request):
        # 取消点赞
        UserId = request.data.get('userId')
        VideoId = request.data.get('videoId')
        user = User.objects.get(account=UserId)
        video = Video.objects.get(id=VideoId)
        if user.video_set.filter(id=VideoId):
            like = video.users.get(account=UserId)
        else:
            return Response(data={'msg': '用户还未点赞'}, status=status.HTTP_400_BAD_REQUEST)
        like.delete()
        video.likeCount = video.likeCount - 1
        video.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

class CommentLikeView(views.APIView):
    authentication_classes = [headerPostAuthentication,headerDeleteAuthentication]
    # 处理评论点赞功能
    def get(self,request):
        # 获取单个点赞信息
        comment = Comment.objects.get(id=request.GET.get("commentId"))

        if comment.users.filter(account=request.GET.get("userId")):
            print(comment.users.filter(account=request.GET.get("userId")))
            return Response(data={'like': 'True'}, status=status.HTTP_200_OK)
        else:
            print(False)
            return Response(data={"like": "False"}, status=status.HTTP_200_OK)

    def post(self,request):
        # 点赞
        UserId=request.data.get('userId')
        CommentId = request.data.get('commentId')
        user = User.objects.get(account=UserId)
        comment = Comment.objects.get(id=CommentId)
        comment.users.add(user)
        comment.like_count = comment.like_count+1
        comment.save()
        return Response(data={'like_count':comment.like_count}, status=status.HTTP_200_OK)

    def delete(self,request):
        # 取消点赞
        UserId = request.data.get('userId')
        CommentId = request.data.get('commentId')
        user = User.objects.get(account=UserId)
        comment = Comment.objects.get(id=CommentId)
        print(user,comment)
        if comment.users.filter(account=UserId):
            like = comment.users.get(account=UserId)
        else:
            print(comment.users.filter(account=UserId))
            return Response(data={'msg': '用户还未点赞'}, status=status.HTTP_400_BAD_REQUEST)
        comment.users.remove(user)
        comment.like_count = comment.like_count - 1
        comment.save()
        return Response(data={'like_count':comment.like_count},status=status.HTTP_204_NO_CONTENT)


def sensitiveWordDetection(sentence,Tree):
    pointerList = []  # 关键词的起始位置和结束位置
    pointer = 0

    def sensitiveWordDetectionAlgorithm(sentence,dict,depth):
        if len(sentence) == 0:  # 句子查找完不再查找
            return False
        char = sentence[0]
        if char in dict.keys():  # 如果有对应节点
            if '#' not in dict[char].keys():
                return sensitiveWordDetectionAlgorithm(sentence[1:],dict[char],depth+1)  # 继续查找
            else:
                sensitiveWordDetectionAlgorithm(sentence[1:], dict[char], depth + 1)  # 即使检测到了也要继续检测，防止检测到ab就不再检测abc。
                pointerList.append([pointer, pointer + depth+1])
        else:
            return False

    for i in range(len(sentence)):
        pointer = i  # 记录检测位置
        sensitiveWordDetectionAlgorithm(sentence[i:],Tree,0)  # 传输的是文本检测位置之后的子串
    return pointerList


def mask(sentence,pointerList):
    result = ''
    lastPointer = [0,0]
    for pointer in pointerList:
        result += sentence[lastPointer[1]:pointer[0]]+'*'*(pointer[1]-pointer[0])
        lastPointer = pointer
    result += sentence[lastPointer[1]:]
    return result


def detect(sentence):
    for ty in ['b','c','m']:  # 禁止关键词，审核关键词，替换关键词
        pointerList = sensitiveWordDetection(sentence,DFATreeType(ty))  # 检测
        if pointerList:
            if ty == 'b':
                return True
            elif ty == 'c':
                return False
            elif ty == 'm':
                return mask(sentence,pointerList)


def contentToReport(data, contentId,type):
    data.update({'respondent':data['sender']})
    data.update({'sender':1})  # 规定第一个用户为官方用户
    data.update({'reason':'检测到审核关键词'})
    data.update({'type':type})
    data.update({'contentId':contentId})
    return data


class CommentView(views.APIView):
    authentication_classes = [headerPostAuthentication]
    # 评论
    def get(self,request):  # 获取一个视频的所有评论 params:VideoId,userId

        VideoId = request.GET.get('VideoId')
        comments = Comment.objects.filter(video=VideoId).order_by("-timestamp")
        likes = []
        for comment in comments:
            likes.append(bool(comment.users.filter(account=request.GET.get("userId"))))
        s = CommentListSerializer(instance=comments,many=True)
        for i in range(len(s.data)):
            s.data[i].update({'like':likes[i]})
        return Response(data=s.data, status=status.HTTP_200_OK)

    def post(self,request):
        content = request.data.get('content')
        data = request.data
        print(data)
        report = False
        detectResult = detect(sentence=content)
        if type(detectResult) == bool:
            if detectResult:
                return Response(data={'msg': '触发屏蔽词，不可发送'})
            else:
                report = True  # 需要在保存后再进行处理
        elif type(detectResult) == str:
            data['content'] = detectResult
        s = CommentSendSerializer(data=data)
        if s.is_valid():
            VideoId = data['video']
            video = Video.objects.get(pk=VideoId)
            video.commentCount = video.commentCount+1
            video.save()
            s_result = s.save()
            if report:
                report = contentToReport(data,s_result.id,'c')
                r = ReportRecordSerializer(data=report)
                if not r.is_valid():
                    return Response(data={'msg': '检测到审核关键词，但是举报失败'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    r.save()
            return Response(data=s.data,status=status.HTTP_201_CREATED)
        return Response(s.errors,status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request):
        try:
            comment = Comment.objects.get(pk=request.data.get('id'))
        except Comment.DoesNotExist:
            return Response(data={"msg": "没有此评论信息"}, status=status.HTTP_404_NOT_FOUND)
        VideoId = request.GET.get('video')
        video = Video.objects.get(VideoId)
        video.commentCount = video.commentCount - 1
        video.save()
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def predict(sentence):
    sentence = ' '.join([array[0] for array in thu.cut(sentence)])
    result = ft.predict(sentence)
    score = 1-result[1][0] if result[0][0]=='__label__0' else result[1][0]
    score = 0 if score<0 else score
    score = 1 if score>1 else score
    score = floor(score/0.2)
    if score == 5:
        score = 4
    return score


class BulletChatView(views.APIView):

    def get(self,request):
        VideoId = request.GET.get('VideoId')
        level = request.GET.get('level',None)
        print("level",level,type(level))
        if level:
            bulletchats = BulletChat.objects.filter(video=VideoId,level__lte=level).order_by("-timestamp")
        else:
            bulletchats = BulletChat.objects.filter(video=VideoId).order_by("-timestamp")
        print(len(bulletchats))
        s = BulletChatListSerializer(instance=bulletchats,many=True)
        return Response(data=s.data,status=status.HTTP_200_OK)

    def post(self,request):
        # 分级为0-4 每20%分割一级
        content = request.data.get('content')
        data = request.data
        report = False
        detectResult = detect(sentence=content)
        if type(detectResult) == bool:
            if detectResult:
                return Response(data = {'msg':'触发屏蔽词，不可发送'})
            else:
                report = True  # 需要在保存后再进行处理
        elif type(detectResult) == str:
            data['content'] = detectResult
        level = predict(content)
        data['level'] = level
        print(data)
        s = BulletChatSendSerializer(data=data)
        if s.is_valid():
            VideoId = data['video']
            video = Video.objects.get(pk=VideoId)
            video.commentCount = video.commentCount + 1
            video.save()
            sResult = s.save()
            if report:
                report = contentToReport(data, sResult.id,'b')
                print(report)
                r = ReportRecordSerializer(data = report)
                print(r)
                if not r.is_valid():
                    return Response(data={'msg':'检测到审核关键词，但是举报失败'},status = status.HTTP_400_BAD_REQUEST)
                else:
                    r.save()
            return Response(data=s.data,status=status.HTTP_201_CREATED)
        return Response(data = {'msg':'弹幕保存失败'},status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request):
        try:
            bulletchat = BulletChat.objects.get(pk=request.data.get('id'))
        except BulletChat.DoesNotExist:
            return Response(data={"msg": "没有此弹幕信息"},status=status.HTTP_404_NOT_FOUND)
        bulletchat.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class VideoView(views.APIView):

    def get(self,request):
        VideoId = request.GET.get('VideoId')
        try:
            video = Video.objects.get(pk=VideoId)
        except Video.DoesNotExist:
            return Response(data={'msg':'视频不见了'},status=status.HTTP_404_NOT_FOUND)
        s = VideoSerializer(instance=video)
        video.ViewCount = video.ViewCount + 1
        video.save()
        return Response(data=s.data,status=status.HTTP_200_OK)


class LoginView(views.APIView):
    def post(self, request):
        user = request.data.get("account")
        pwd = request.data.get("password")

        user_object = User.objects.filter(account=user,password = pwd).first()
        if not user_object:
            return Response({"code":200,"msg":"用户名或密码错误"})

        timestamp = floor(time())
        HEADER = {
              "alg": "HS256",
              "typ": "JWT"
            }
        payload = {
              "sub": user,
              "iat": timestamp
            }
        print(payload)
        token = jwt.encode(payload=payload, key=settings.SECRET_KEY, algorithm='HS256', headers=HEADER)

        return Response({"jwt":token,'account':user})

class registerView(views.APIView):
    def post(self,request):
        account = request.data.get("account")
        name = request.data.get("name")
        pwd = request.data.get("password")
        pwd2 = request.data.get("passwordConfirm")
        if pwd!=pwd2:
            return Response({'msg':'两次输入密码不一致','code':202},status=status.HTTP_406_NOT_ACCEPTABLE)
        elif User.objects.filter(account=account):
            return Response({'msg':'账号冲突','code':203})
        else:
            s = RegisterSerializer(data={'name':name,'password':pwd,'account': account})
            if s.is_valid():
                s2 = s.save()
                return Response({'account': s2.account},status=status.HTTP_201_CREATED)
        return Response({'msg':'注册格式出错'},status=status.HTTP_400_BAD_REQUEST)



# 后台内容

class BackgroundLoginView(views.APIView):

    def post(self, request):
        user = request.data.get("account")
        pwd = request.data.get("password")

        user_object = User.objects.filter(account=user, password=pwd).first()
        if not user_object:
            return Response({"code": 200, "msg": "用户名或密码错误"})
        if user_object.Identity !='r' and user_object.Identity != 'k':
            return Response({"code": 201, "msg": "权限不足"})
        timestamp = floor(time())
        HEADER = {
            "alg": "HS256",
            "typ": "JWT"
        }
        payload = {
            "sub": user,
            "iat": timestamp
        }
        token = jwt.encode(payload=payload, key=settings.SECRET_KEY, algorithm='HS256', headers=HEADER).encode('utf-8')

        return Response({"msg": token})


def DFA_Generator(word,dict):
    if len(word) == 0:  # 空字符串直接退出
        return
    char = word[0]
    if char in dict.keys():  # 如果原来有节点，向下一层遍历
        DFA_Generator(word[1:],dict[char])
    else:
        dict.update({char:{}})  # 原来没有节点，加入节点
        DFA_Generator(word[1:],dict[char])  # 向下一层遍历
    if len(word) == 1:  # 如果是最后一个字符，加入终点
        dict[char].update({'#': ''})

typeToShowType = {'c':'审核关键词','b':'禁止关键词','m':'替换关键词'}

class BannedWordView(views.APIView):

    # 参数：类型type 页数page 每页个数pageNum
    def get(self,request):
        type = request.query_params.get("type",None)
        if type:
            BannedWords = BannedWord.objects.filter(type = type )
        else:
            BannedWords = BannedWord.objects.all()
        count = BannedWords.count()
        pageNum = request.GET.get('pageNum',None)
        if pageNum:
            if int(pageNum)<=MAX_PAGE_SIZE:
                paginalNumber = ceil(count/int(pageNum))
            else:
                return Response({"code":'402','msg':'每页请求数量超过最大数量'})
        else:
            paginalNumber = ceil(count / DEFAULT_PAGE_NUM)
        page = MyPageNumberPagination()
        res = page.paginate_queryset(BannedWords, request, self)
        ser = BannedWordSerializer(res, many=True)
        # if pages.num_pages<=page:
        #     return Response(data={'code':400,"msg":"请求页数超过最大值"},status=status.HTTP_400_BAD_REQUEST)
        return Response({'data':ser.data,'maxPage':paginalNumber},status=status.HTTP_200_OK)

    # 参数：要删除的屏蔽词的索引值id
    def delete(self,request):
        id = request.query_params.get("id")
        word = BannedWord.objects.get(pk=id)
        wordWord = word.word
        wordType = word.type
        rootIndex = -1  # 未找到
        tree = DFATreeType(word.type)
        for index in range(len(word.word)):
            tree = tree[word.word[index]]  # 向下遍历
            if len(tree.keys()) == 1:  # 单一节点
                if rootIndex == -1:  # 如果没有找到节点，认定在这里截断
                    rootIndex = index
                else:  # 连续的单一节点从离根最近的节点开始截断
                    continue
            else:
                rootIndex = -1
        if rootIndex == -1:  # 没有单枝，去掉最后的结束符号
            del tree['#']
        else:
            tree = DFATreeType(word.type)
            for i in range(rootIndex):  # 找到截断节点的位置
                tree = tree[word.word[i]]
            del tree[word.word[rootIndex]]  # 截断
        word.delete()  # 数据库的数据也同时删除
        return Response(data={'msg':f'已删除类型为{typeToShowType[wordType]}，内容为{wordWord}的关键词'},status=status.HTTP_204_NO_CONTENT)

    # 参数：添加的新词word,新词的屏蔽类型 type
    def post(self,request):
        word = request.query_params.get("word")
        type = request.query_params.get("type")
        if WordFrequency.objects.filter(word = word):
            _word = WordFrequency.objects.filter(word = word).first()
            _word.delete()
        s = BannedWordPostSerializer(data=request.query_params)
        if s.is_valid():
            DFA_Generator(word, DFATreeType(type))
            s.save()
            return Response(data=f"{word} 已添加，类型为{type}",status=status.HTTP_201_CREATED)
        return Response(s.errors,status=status.HTTP_400_BAD_REQUEST)

    # 参数：要删去的旧词主键id，要添加的新词word,新词的类型type
    def put(self,request):
        newWord = request.query_params.get("word")
        type = request.query_params.get("type")
        id = request.query_params.get("id")
        oldWord = BannedWord.objects.get(pk=id)
        oldType = oldWord.type
        rootIndex = -1
        tree = DFATreeType(oldWord.type)
        for index in range(len(oldWord.word)):
            tree = tree[oldWord.word[index]]
            if len(tree.keys()) == 1:
                if rootIndex == -1:
                    rootIndex = index
                else:
                    continue
            else:
                rootIndex = -1
        if rootIndex == -1:  # 没有单枝，去掉最后的结束符号
            del tree['#']
        else:
            tree = DFATreeType(oldWord.type)
            for i in range(rootIndex):
                tree = tree[oldWord.word[i]]
            del tree[oldWord.word[rootIndex]]
        DFA_Generator(newWord, DFATreeType(type))
        if newWord == oldWord.word:  # 如果词没变就只修改类型
            oldWordType = oldWord.type
            oldWord.type = type
            oldWord.save()
            return Response(data={"msg":f"已将{oldWord.word}从{oldWordType}修改为{type}"})
        else:
            oldWord.delete()
            addWord = {
                "word":newWord,
                "type":type
            }
            addWord = BannedWordSerializer(data=addWord)
            if addWord.is_valid():
                addWord.save()
                return Response(data={"msg":f"已将类型是{oldType}的{oldWord.word}修改为类型是{type}的{newWord}"},status=status.HTTP_200_OK)
            return Response(data=addWord.errors,status = status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def searchBannedWord(request): # TODO 搜索没做呢
    content = request.GET.get("content")
    type = request.GET.get("type")
    if type:
        BannedWords = BannedWord.objects.filter(type=type)
    else:
        BannedWords = BannedWord.objects.all()

    page = request.query_params.get("page")
    pageNum = request.query_params.get("pageNum")

    pages = Paginator(BannedWords, pageNum)
    if pages.num_pages <= page:
        return Response(data={'code': 400, "msg": "请求页数超过最大值"}, status=status.HTTP_400_BAD_REQUEST)
    return Response(data={"page": pages.page(page), "num_pages": pages.num_pages}, status=status.HTTP_200_OK)




class DFATreeView(views.APIView):

    def post(self,request):
        with open("utils/DFAClassified.json", "w") as jsonFile:
            json.dump(DFATree, jsonFile)
        return Response({'msg':"索引已保存至文件，修改生效"})

    def get(self,request):
        types = ['b', 'c', 'm']  # 禁止关键词，审核关键词，替换关键词
        readWords = []

        def readTree(tree, word):  #
            for branch, _ in tree.items():
                if branch != '#':  # 未找到
                    readTree(tree[branch], word + branch)  # 向子树查找， 前缀与节点拼接为新前缀
                if branch == '#':  # 找到
                    readWords.append(word)

        word = ''
        for i in range(3):
            readWords = []
            wordList = [word.word for word in BannedWord.objects
                .filter(type=types[i])]  # 按类型查找
            tree = DFATreeType(types[i])
            readTree(tree, word)
            if wordList == readWords:
                continue
            else:
                print(readWords)
                print(wordList)
                return Response({"msg": '检测失败'})

        return Response({'msg': '检测成功！'}, status=status.HTTP_200_OK)

    def patch(self,request):  # TODO 改成只需要加减有差异的词
        global DFATree,checkDFATree,maskDFATree,bannedDFATree
        types = ['b', 'c', 'm']
        indexs = ['banned','check','mask']
        Tree = {}
        for i in range(3):
            tree = {}
            wordList = [word.word for word in BannedWord.objects.filter(type=types[i])]
            for word in wordList:
                DFA_Generator(word,tree)
            Tree.update({indexs[i]:tree})
        settings.GLOBAL_VARIABLES['DFATree'] = Tree
        DFATree = settings.GLOBAL_VARIABLES['DFATree']
        checkDFATree = DFATree["check"]
        maskDFATree = DFATree['mask']
        bannedDFATree = DFATree['banned']
        return Response(data={"msg":'重构字典树完成'},status=status.HTTP_200_OK)


class ReportRecordView(views.APIView):
    authentication_classes = [headerPostAuthentication]
    # 状态 state 类型 type 每页个数 pageNum 第page页
    def get(self,request):
        state = request.GET.get("state",None)
        type = request.GET.get("type",None)
        if not state and not type:
            records = ReportRecord.objects.all()
        elif state and type:
            records = ReportRecord.objects.filter(state=state,type=type)
        elif type:
            records = ReportRecord.objects.filter(type=type)
        else:
            records = ReportRecord.objects.filter(state=state)
        count = records.count()
        pageNum = request.GET.get('pageNum', None)
        if pageNum:
            if int(pageNum) <= MAX_PAGE_SIZE:
                paginalNumber = ceil(count / int(pageNum))
            else:
                return Response({"code": '402', 'msg': '每页请求数量超过最大数量'})
        else:
            paginalNumber = ceil(count / DEFAULT_PAGE_NUM)
        page = MyPageNumberPagination()
        res = page.paginate_queryset(records,request,self)
        ser = ReportRecordGetSerializer(res,many=True)
        return Response({'data':ser.data,'maxPage':paginalNumber},status=status.HTTP_200_OK)

    # 举报人sender 举报理由reason 举报类型（弹幕或评论）type 举报内容的主键 id
    def post(self,request):  # 前台举报
        sender = request.data.get("sender")
        reason = request.data.get("reason")
        type = request.data.get("type")
        id = request.data.get("id")
        if type == 'c':
            Content = Comment.objects.get(pk=id)
        elif type == 'b':
            Content = BulletChat.objects.get(pk=id)
        else:
            return Response(data={"code":500,"msg":"类型有效值为c或b"},status=status.HTTP_400_BAD_REQUEST)
        print(Content.video.id)
        print(Content.sender.account)
        Report = {
            "sender":sender,
            "respondent":Content.sender.account,
            "video":Content.video.id,
            "content":Content.content,
            "contentId":id,
            "type":type,
            "reason":reason
        }
        s = ReportRecordSerializer(data=Report)
        if s.is_valid():
            s.save()
            return Response(data="举报已提交",status=status.HTTP_201_CREATED)
        return Response(data=s.errors,status = status.HTTP_400_BAD_REQUEST)

    # body:举报记录id 举报惩罚deal 惩罚时间 time
    def patch(self,request):  # 后台解决
        period = {'三天':259_200,'一周':604_800,'一月':2_592_000}  # 一月：30天
        id = request.data.get('id')
        deal = request.data.get('deal')
        bannedTime = request.data.get('time',None)
        report = ReportRecord.objects.get(pk=id)
        if report.state == 'a' or report.state == 'r':
            return Response({'code':600,'msg':'请不要重复处理'},status=status.HTTP_400_BAD_REQUEST)
        # 加入训练集
        trainSentences.append(report.content)
        # 词频统计
        words = thu.cut(report.content, text=True)
        words = words.split(' ')
        for word in words:
            if word in safeWords:
                continue
            try:
                frequency = WordFrequency.objects.get(word=word)
                frequency.frequency+=1
                frequency.save()
            except WordFrequency.DoesNotExist:
                if detect(word)==None:
                    s = WordFrequencySerializer(data={'word':word})
                    if s.is_valid():
                        s.save()

        respondent = report.respondent
        if deal=='封禁':
            respondent.identity = 'c'
            respondent.save()
            report.deal=deal
        elif deal=='禁言':
            if bannedTime == '三天':
                respondent.banned = timezone.now() + datetime.timedelta(days=3)
            elif bannedTime == '一周':
                respondent.banned = timezone.now() + datetime.timedelta(weeks=1)
            elif bannedTime == '一月':
                respondent.banned = timezone.now() + datetime.timedelta(days = 30)
            respondent.identity = 'b'
            respondent.save()
            report.deal=deal+' '+bannedTime
        elif deal=='删除':
            print(type)
            if report.type=='c':
                comment = Comment.objects.get(pk=report.contentId)
                comment.delete()
            elif report.type=='b':
                bulletchat = BulletChat.objects.get(pk=report.contentId)
                bulletchat.delete()
            else:
                return Response({'code':500,'msg':'不支持的类型'},status = status.HTTP_400_BAD_REQUEST)
            report.deal=deal
        else:
            return Response({'code':500,'msg':'不支持的方法'},status=status.HTTP_400_BAD_REQUEST)
        report.state = 'a'
        reports = ReportRecord.objects.filter(type=report.type,contentId = report.contentId)
        for _report in reports:
            _report.state = 'a'
            _report.save()
        report.save()
        return Response({'msg':'处理成功'},status=status.HTTP_200_OK)

    # params:举报记录id
    def delete(self,request):
        id = request.GET.get("id")
        report = ReportRecord.objects.get(pk=id)
        report.state = 'r'  # 将举报记录修改为已拒绝（reject）状态
        reports = ReportRecord.objects.filter(type=report.type, contentId=report.contentId)
        for _report in reports:
            _report.state = 'r'
            _report.save()
        report.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# 分析并找出出现次数最多的词,分析过程在举报处理部分
class WordFrequencyView(views.APIView):
    # 无参数
    def get(self,request):  # 前十个词
        words = WordFrequency.objects.all().order_by('-frequency')[:10]
        words = WordFrequencyGetSerializer(instance=words,many=True)
        return Response(data=words.data,status = status.HTTP_200_OK)

    # word
    def post(self,request):  # 加入敏感词直接使用敏感词的api，这个是加入到安全的api。
        safeWords.append(request.data.get('word'))
        word = WordFrequency.objects.get(word = request.data.get('word'))
        word.delete()
        with open('utils/safeWords.json','w') as jsonFile:
            json.dump(safeWords,jsonFile)
        return Response(status=status.HTTP_200_OK)
    
@api_view(['post'])
def saveTrain(request):
    global trainSentences
    with open('../train.txt','a',encoding="utf-8") as f:
        f.writelines(trainSentences)
        f.writelines()
        trainSentences = []  # 避免重复加入


@api_view(['get'])
def statistics(request):
    all_num = ReportRecord.objects.all().count()
    not_solve_num = ReportRecord.objects.filter(state='p').count()
    solve_and_reject_num = all_num-not_solve_num
    reject_num = ReportRecord.objects.filter(state='r').count()
    solve_num = ReportRecord.objects.filter(state='a').count()
    all_word_num = BannedWord.objects.all().count()
    banned_word_num = BannedWord.objects.filter(type='b').count()
    mask_word_num = BannedWord.objects.filter(type='m').count()
    check_word_num = BannedWord.objects.filter(type='c').count()

    return Response(data={"all_num":all_num,"solve_num":solve_num,"not_solve_num":not_solve_num,
                          "solve_and_reject_num":solve_and_reject_num,'reject_num':reject_num,
                          "all_word_num":all_word_num,'banned_word_num':banned_word_num,
                          'mask_word_num':mask_word_num,'check_word_num':check_word_num})