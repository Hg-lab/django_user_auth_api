import sys

from django.http import JsonResponse
from rest_framework import status


def error_404(request, exception):
    type_, value, traceback = sys.exc_info()
    message = {
                '404 error type': str(type_)
               }
    response = JsonResponse(data=message, status=status.HTTP_404_NOT_FOUND)
    return response


def error_500(request):
    type_, value, traceback = sys.exc_info()
    message = {
                '500 error type': str(type_)
               }
    response = JsonResponse(data=message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return response
