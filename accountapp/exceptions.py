from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_408_REQUEST_TIMEOUT


class InvalidPhoneException(Exception):
    status = HTTP_400_BAD_REQUEST
    message = 'invalid phone number'


class TimeoutException(Exception):
    status = HTTP_408_REQUEST_TIMEOUT
    message = 'request timeout'
