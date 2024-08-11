from django.utils.deprecation import MiddlewareMixin

class HttpResponseCustomHeader(MiddlewareMixin):
    def process_response(self, request, response):
        response["Access-Control-Allow-Headers"] = "Content-Type"
        response["Access-Control-Allow-Origin"] = "http://localhost:5173"
        return response
