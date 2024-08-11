from rest_framework import serializers
from .models import User,Video,Comment,BulletChat,BannedWord,ReportRecord,WordFrequency


MEDIA_ADDR = "http://127.0.0.1:8000/media/"


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['account','name','identity','gender']


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name','password','account']


class LikeSerializer(serializers.Serializer):
    UserId = serializers.IntegerField(read_only=True)
    VideoId = serializers.IntegerField(read_only=True)

    def save(self):
        UserId = self.validated_data['UserId']
        VideoId = self.validated_data['VideoId']
        user= User.objects.get(id=UserId)
        video = Video.objects.get(id=VideoId)
        video.users.add(user)


class CommentListSerializer(serializers.ModelSerializer):

    sender = UserSerializer()

    class Meta:
        model = Comment
        fields = ['id','content','timestamp','like_count','sender']


class CommentSendSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['content','video','sender']


class BulletChatListSerializer(serializers.ModelSerializer):
    text = serializers.CharField(source='content')
    class Meta:
        model = BulletChat
        fields = ['content','timestamp','time','sender','level','text','id']


class BulletChatSendSerializer(serializers.ModelSerializer):
    class Meta:
        model = BulletChat
        fields = ['content','time','video','sender','level']


class VideoSerializer(serializers.ModelSerializer):
    producer = UserSerializer()

    class Meta:
        model = Video
        fields = ['name','producer','introduction','timestamp','ViewCount','likeCount','videoName','commentCount','id']


class BannedWordSerializer(serializers.ModelSerializer):

    class Meta:
        model = BannedWord
        fields = '__all__'


class BannedWordPostSerializer(serializers.ModelSerializer):

    class Meta:
        model = BannedWord
        exclude = ['id']


class ReportRecordSerializer(serializers.ModelSerializer):

    class Meta:
        model = ReportRecord
        exclude = ["timestamp","state","deal"]


class ReportRecordGetSerializer(serializers.ModelSerializer):
    sender = UserSerializer()
    respondent = UserSerializer()
    video=VideoSerializer()

    class Meta:
        model = ReportRecord
        fields = '__all__'


class WordFrequencySerializer(serializers.ModelSerializer):

    class Meta:
        model = WordFrequency
        exclude = ['frequency']


class WordFrequencyGetSerializer(serializers.ModelSerializer):

    class Meta:
        model = WordFrequency
        fields = '__all__'
