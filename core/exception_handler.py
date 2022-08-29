import sys

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    type_, value, traceback = sys.exc_info()
    handlers = {
        'ValidationError': _handle_generic_error,
        'Http404': _handle_generic_error,
        'PermissionDenied': _handle_generic_error,
        'NotAuthenticated': _handle_authentication_error,
    }
    invalid_data_error_type_handler = {
        # Invalid data
        'TypeError': status.HTTP_500_INTERNAL_SERVER_ERROR,
        'AttributeError': status.HTTP_500_INTERNAL_SERVER_ERROR,
        'KeyError': status.HTTP_500_INTERNAL_SERVER_ERROR,
    }

    response = exception_handler(exc, context)

    if response is not None:
        response.data['status_code'] = response.status_code

    # for invalid data error type
    else :
        type_, value, traceback = sys.exc_info()
        for error_type in invalid_data_error_type_handler.keys():
            if error_type in str(type_): # str(type) = <class 'XXXXXXError'>
                data = {
                    "message": str(type_) + " - " + str(exc)
                }
                return Response(data, status=invalid_data_error_type_handler[error_type])

    exception_class = exc.__class__.__name__

    if exception_class in handlers:
        return handlers[exception_class](exc, context, response)
    return response


def _handle_authentication_error(exc, context, response):
    response.data['status_code'] = response.status_code
    response.data = {
        "message": "Please login to proceed"
    }

    return response


def _handle_generic_error(exc, context, response):
    response.data['status_code'] = response.status_code
    return response