from rest_framework.views import APIView


class OrderView(APIView):
    def check_permissions(self, request):
        permissions = self.get_permissions()
        for permission in permissions:
            if permission.has_permission(request,self):
                return
        else:
            self.permission_denied(
                request,
                message=getattr(permissions[0],'message',None),
                code = getattr(permissions[0], 'code', None)
            )