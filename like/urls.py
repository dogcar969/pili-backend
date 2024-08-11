from django.urls import path
from . import views

urlpatterns = [
    path('like/',views.VideoLikeView.as_view(), name='videolike'),
    path('comment/',views.CommentView.as_view(),name='comment'),
    path('commentLike/',views.CommentLikeView.as_view(),name='commentLike'),
    path('bulletchat/',views.BulletChatView.as_view(),name='bulletchat'),
    path('video/',views.VideoView.as_view(),name='video'),
    path('word/',views.BannedWordView.as_view(),name='word'),
    path('tipOff/',views.ReportRecordView.as_view(),name="report"),
    path('tree/',views.DFATreeView.as_view(),name='tree'),
    path('stream_video/', views.stream_video, name='stream_video'),
    path('register/', views.registerView.as_view() , name="register"),
    path("login/",views.LoginView.as_view(), name='login'),
    path("user/",views.UserView.as_view(), name='user'),
    path('statistics/',views.statistics,name='statistics'),
    path('frequency/',views.WordFrequencyView.as_view(),name='frequency')
]