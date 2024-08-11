# pili 后端

这是**基于自然语言处理的影视播放平台的设计与实现**的后端部分

## 技术栈

Django

Django REST Framework

PostgreSQL

FastText

## 功能

视频传输，评论，点赞，弹幕，关键词过滤，语意过滤，举报，管理关键词，管理举报，用户认证，禁言，封禁

## 算法

使用DFA算法进行关键词匹配

使用fastText进行基于文意的恶意评级。

## 文件

drf/settings 设置

drf/urls like/urls url设置

like/models 数据结构配置

like/views 接口实现