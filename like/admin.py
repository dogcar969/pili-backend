from django.contrib import admin

from .models import User,Video,Comment,BulletChat,ReportRecord
# Register your models here.
admin.site.register(User)
admin.site.register(Video)
admin.site.register(Comment)
admin.site.register(BulletChat)
admin.site.register(ReportRecord)