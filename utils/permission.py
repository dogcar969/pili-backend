from rest_framework.permissions import BasePermission

class viewPermission(BasePermission):
    message = {"code": 300, "msg": "无权访问"}  # 未通过时的信息，由框架自动调用

    def has_permission(self, request, view):
        if request.user.identity == 'v':
            return True
        return False

class reportPermission(BasePermission):
    message = {"code": 300, "msg": "无权访问"}

    def has_permission(self, request, view):
        if request.user.identity == 'r':
            return True
        return False

class keywordPermission(BasePermission):
    message = {"code": 300, "msg": "无权访问"}

    def has_permission(self, request, view):
        if request.user.identity == 'k':
            return True
        return False

class bannedPermission(BasePermission):
    message = {"code": 300, "msg": "无权访问"}

    def has_permission(self, request, view):
        if request.user.identity == 'b':
            return False
        return True