from django.db import models
from django.core.validators import MinValueValidator,MaxValueValidator
import uuid
from django.utils import timezone
import datetime
import os
from drf import settings


MEDIA_ADDR = "http://127.0.0.1:8000/media/"


class User(models.Model):
    account = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=10)
    password = models.CharField(max_length=64,verbose_name='加密后的密码',
                          default='8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92')
    IdentityType = {
        'v': 'viewer',
        'r': 'report',
        'k': 'keyword',
        'b': 'banned',
        'c':'close'
    }
    identity = models.CharField(max_length=1,choices=IdentityType,default='v',verbose_name='身份')
    GenderType = {
        'w' : 'woman',
        'm' : 'man',
        's' : 'secret'
    }
    gender = models.CharField(max_length=1,choices=GenderType,default='s',verbose_name='性别')
    defaultTime = datetime.datetime.combine(datetime.date(2024, 1, 1), datetime.time(0, 0, 0))
    # 一个已经过去的时间，如果是这个时间就是没有封过
    banned = models.DateTimeField(default=defaultTime)


    def __str__(self):
        return self.name

class Video(models.Model):
    name = models.CharField(max_length=10)
    producer = models.ForeignKey(User,on_delete=models.DO_NOTHING,related_name='producer',default='1')
    introduction = models.CharField(default='这个视频还没有简介哦',max_length=2000,verbose_name='视频简介')
    timestamp = models.DateTimeField(verbose_name='发送时间',auto_now_add=True)
    ViewCount = models.IntegerField(default=0,verbose_name='播放量',validators=[MinValueValidator(0)])
    users = models.ManyToManyField(User,blank=True)
    likeCount = models.PositiveIntegerField(default=0,validators=[MinValueValidator(0)])
    commentCount = models.PositiveIntegerField(default=0,validators=[MinValueValidator(0)])
    videoName = models.CharField(max_length=100,default="SampleVideo_1280x720_10mb.mp4")
    def __str__(self):
        return self.name

class Comment(models.Model):
    content = models.CharField(max_length=2000)
    timestamp = models.DateTimeField(verbose_name='发送时间',auto_now_add=True)
    video = models.ForeignKey(Video,on_delete=models.CASCADE)
    sender = models.ForeignKey(User,on_delete=models.CASCADE)
    like_count = models.PositiveIntegerField(default=0)
    users = models.ManyToManyField(User,blank=True,related_name='like')  # 点赞的人

    def __str__(self):
        return self.content

class BulletChat(models.Model):
    content = models.CharField(max_length=100)
    timestamp = models.DateTimeField(verbose_name='发送时间',auto_now_add=True)
    time = models.IntegerField(verbose_name='弹幕在视频中出现的时间')
    video = models.ForeignKey(Video,on_delete=models.CASCADE)
    level = models.IntegerField(verbose_name='屏蔽等级',default='0',validators=[MinValueValidator(0,'等级不可小于0'),MaxValueValidator(4,'等级不可大于5')])
    sender = models.ForeignKey(User,on_delete=models.CASCADE)

    class Meta:
        verbose_name = '弹幕'

    def __str__(self):
        return str(self.sender.name)+":"+self.content

class BannedWord(models.Model):
    word = models.CharField(max_length=255,help_text="违禁词",verbose_name='违禁词',unique=True)
    type_explain = {
        'b': 'banned',
        'm': 'mask',
        'c': 'check'
    }
    type = models.CharField(choices=type_explain,default='b')

    class Meta:
        verbose_name = "违禁词"

    def __str__(self):
        return self.word + " type: " +self.type_explain[self.type]

# todo 多人处理？
class ReportRecord(models.Model):  # 由于要同时处理弹幕和评论，所以不能设置特定表的外键
    sender = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,related_name="sender")
    respondent = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,related_name="respondent")  # 被举报人
    content = models.CharField(max_length=2000)
    contentId = models.IntegerField(validators=[MinValueValidator(0,'主键不可小于0')])
    video = models.ForeignKey(Video,on_delete=models.SET_NULL,null=True)
    typeChoice = {
        'c':'comment',
        'b':'bulletchat'
    }
    type = models.CharField(max_length=1,choices=typeChoice)
    reason = models.CharField(max_length=100)
    timestamp = models.DateTimeField(verbose_name='发送时间',auto_now_add=True)
    stateChoice = {
        "p":'pending',  # 待解决
        "a":'approve',  # 已解决
        'r':'reject'    # 已拒绝（举报内容没有问题）
    }
    state = models.CharField(max_length=1,choices = stateChoice,default='p')
    deal = models.CharField(max_length=100,null=True)  # 举报的处理方法


class WordFrequency(models.Model):  # 词频分析
    word = models.CharField(max_length=100,unique=True)
    frequency = models.IntegerField(validators=[MinValueValidator(0,'频数不可小于0')],default=1)

