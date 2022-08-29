# Create your views here.
from django.db import transaction
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from jwt import InvalidSignatureError
from rest_framework import status
from rest_framework.decorators import permission_classes
from rest_framework.exceptions import NotAuthenticated, NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accountapp import models
from accountapp.exceptions import InvalidPhoneException, TimeoutException
from accountapp.models import User
from accountapp.open_api_params import swagger_params
from accountapp.permissions import IsNotAuthenticated
from accountapp.serializers import UserModelSerializer, CustomTokenObtainPairSerializer, AuthCodeModelSerializer, \
    SendAuthCodeSerializer, UserGettingInfoSerializer
from core.interface import send_sms, send_email
from core.jwt_utils import encode_for_unauthenticated_user, decode
from core.utils import data_masking


# For duplication check for each field, find password
# user_info_type can be type only in allowed_info_types
# parameters: user_info_type, user_info
class CheckInfoExistsAPIView(APIView):

    @swagger_auto_schema(request_body=swagger_params['get_params_CheckInfoExistsAPIView'])
    def post(self, request):
        allowed_info_types = ['username', 'nickname', 'phone', 'email', ]
        try:
            user_info_type = request.data['user_info_type']
            user_info = request.data['user_info']

            if user_info_type not in allowed_info_types:
                raise NotFound

            user = User.objects.get(**{user_info_type: user_info})

            message = 'this exists'
            return Response({"message": message}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            message = 'not exist'
            return Response({"message": message}, status=status.HTTP_204_NO_CONTENT)
        except NotFound:
            message = "invalid info type"
            return Response({"message": message}, status=status.HTTP_404_NOT_FOUND)

# parameters
# Required: auth type, phone number
# Optional: user info type, user info
@permission_classes([IsNotAuthenticated])
class SendAuthCodeAPIView(APIView):

    @swagger_auto_schema(request_body=swagger_params['get_params_SendAuthCodeAPIView'])
    def post(self, request):
        # When find password or something needs more credentials, 'auth_type' must be in 'need_more_user_info'
        # When find password, 'auth-type' must be 'find-password'
        allowed_auth_types = {'only_need_phone': ['sign-up'], 'need_more_user_info': ['find-password']}
        types = []
        for type_list in allowed_auth_types.values():
            for type in type_list:
                types.append(type)

        try:
            auth_type = request.data['auth_type']
            phone_data = {'phone': request.data['phone']}

            if auth_type not in types:
                return Response({"message": "Not allowed authentication type"}, status=status.HTTP_400_BAD_REQUEST)


            send_auth_code_serializer = SendAuthCodeSerializer(data=request.data)

            if auth_type in allowed_auth_types['need_more_user_info']:
                user_info_type = request.data['user_info_type']
                user_info = request.data['user_info']

                # Check if user exists. If user wants to password, user must exist.
                User.objects.get(**{user_info_type: user_info}, phone=phone_data['phone'])  # Exception: User.DoesNotExist

            if send_auth_code_serializer.is_valid():
                auth_code = send_auth_code_serializer.save(phone_data)
                return Response({"code": str(auth_code.code)}, status=status.HTTP_201_CREATED)

        except User.DoesNotExist:
            return Response({"message": "User matching id(or email) and phone does not exist"},
                            status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(send_auth_code_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# parameters
# Required: phone number, authentication code
@permission_classes([IsNotAuthenticated])
class AuthByCodeAPIView(APIView):

    @swagger_auto_schema(request_body=swagger_params['get_params_AuthByCodeAPIView'])
    def post(self, request):
        timeout = {'time': 3, 'unit': 'minutes'}

        try:
            phone = request.data['phone']
            code = request.data['code']

            # Phone number doesn't exist
            if models.AuthCode.objects.filter(phone=phone).first() is None:
                raise InvalidPhoneException

            # Check phone and code. If user get authentication by code, this must exist
            models.AuthCode.objects.get(phone=phone, code=code)  # Exception: models.AuthCode.DoesNotExist

            # Check timeout after getting authentication code
            if models.AuthCode.check_limit_time(phone, timeout) is False:
                raise TimeoutException

            # Make it 'authenticated'
            models.AuthCode.objects.filter(phone=phone).update(is_authenticated=True)
            return Response({"message": "authenticated successfully"}, status=status.HTTP_200_OK)

        except models.AuthCode.DoesNotExist:
            message = 'invalid code'
            return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)
        except InvalidPhoneException as e:
            return Response({"message": e.message}, status=e.status) # status code : 400
        except TimeoutException as e:
            return Response({"message": e.message}, status=e.status) # status code : 408


@permission_classes([IsNotAuthenticated])
class SignUpAPIView(APIView):

    @swagger_auto_schema(request_body=swagger_params['get_params_SignUpAPIView'])
    @transaction.atomic()
    def post(self, request):
        timeout = {'time': 5, 'unit': 'minutes'}
        try:
            request_user = UserModelSerializer(data=request.data)
            phone = request.data['phone']

            # Check if authenticated before trying siging up.
            # 5 mins after authentication, it is not valid
            if not models.AuthCode.check_authenticated(phone, timeout):
                raise NotAuthenticated

            if request_user.is_valid(): # if not : status code 400
                new_user = request_user.create(request_user.validated_data)

                # Delete this user authentication code, for preventing re-use (when find password)
                models.AuthCode.objects.filter(phone=new_user.phone).delete()

                success_response = Response(
                    {"message": "User nickname('%s') is created successfully" % new_user.nickname},
                    status=status.HTTP_201_CREATED)
                return success_response

            # Fail: request_user is not valid
            # But, Model Serializer automatically raise exception
            else:
                return Response(request_user.errors, status=status.HTTP_400_BAD_REQUEST)
        except NotAuthenticated:
            message = "not authenticated"
            return Response({"message": message}, status=status.HTTP_403_FORBIDDEN)


@permission_classes([IsNotAuthenticated])
class SignInWithIdAPIView(APIView):

    @swagger_auto_schema(request_body=swagger_params['get_params_SignInWithIdAPIView'])
    def post(self, request):
        response = sign_in(request, 'username')
        return response


@permission_classes([IsNotAuthenticated])
class SignInWithEmailAPIView(APIView):

    @swagger_auto_schema(request_body=swagger_params['get_params_SignInWithEmailAPIView'])
    def post(self, request):
        response = sign_in(request, 'email')
        return response


@permission_classes([IsNotAuthenticated])
class SignInWithPhoneAPIView(APIView):

    @swagger_auto_schema(request_body=swagger_params['get_params_SignInWithPhoneAPIView'])
    def post(self, request):
        response = sign_in(request, 'phone')
        return response


@permission_classes([IsNotAuthenticated])
def sign_in(request, info_type):
    try:
        allowed_info_types = ['username', 'email', 'phone', ]
        if info_type not in allowed_info_types:
            raise NotFound

        user_info = request.data.get(str(info_type))
        password = request.data.get('password')

        # Validate User
        user = User.objects.get(**{info_type: user_info})
        if not user.check_password(password):
            raise User.DoesNotExist

        # Obtain token
        token = CustomTokenObtainPairSerializer.get_token(user)
        refresh_token = str(token)
        access_token = str(token.access_token)

        # success
        return Response({"message": "signed in successfully",
                         "refresh_token": refresh_token,
                         "access_token": access_token},
                        status=status.HTTP_200_OK
                        )

    except User.DoesNotExist:
        message = "invalid id or password"
        return Response({"message": message}, status=status.HTTP_403_FORBIDDEN)
    except NotFound:
        message = "invalid sign-in type"
        return Response({"message": message}, status=status.HTTP_404_NOT_FOUND)


@permission_classes([IsAuthenticated])
class MyAccountInformationAPIView(APIView):
    @swagger_auto_schema(manual_parameters=swagger_params['get_params_MyAccountInformationAPIView'])
    def get(self, request):
        requested_user = request.user
        username = requested_user.username
        user = User.objects.get(username=username)
        if user is not None:
            user_data = UserGettingInfoSerializer(user).data
            return Response({"user": user_data}, status=status.HTTP_200_OK)

        # Actually, This is not needed.
        # settnings.REST_FRAMEWORK.DEFAULT_AUTHENTICATION_CLASSES ->
            # successful_authenticator : Simple JWT
            # Simple JWT identifies requqest.user.
        return Response({"message": "fail"}, status=status.HTTP_400_BAD_REQUEST)


@permission_classes([IsNotAuthenticated])
class FindPasswordAPIView(APIView):

    @swagger_auto_schema(request_body=swagger_params['get_params_FindPasswordAPIView'])
    def post(self, request):
        allowed_info_types = ['username', 'email']
        timeout = {'time': 5, 'unit': 'minutes'}
        try:
            user_info_type = request.data['user_info_type']
            user_info = request.data['user_info']
            phone = request.data['phone']

            # Check invalid access
            if user_info_type not in allowed_info_types:
                raise InvalidSignatureError

            # Check if authenticated before trying siging up.
            # 5 mins after authentication, it is not valid
            if not models.AuthCode.check_authenticated(phone, timeout):
                raise NotAuthenticated # HTTP_403_FORBIDDEN

            # When doesn't exist, raise exception
            user = User.objects.get(**{user_info_type: user_info}, phone=phone)  # Exception: User.DoesNotExist

            # This token for: Authenticated phone number can try to change other's password
            token_for_password_change = encode_for_unauthenticated_user(user, 'password_change')
            return Response({"message": "Authenticated",
                             "token_for_password_change": token_for_password_change},
                            status=status.HTTP_200_OK)

        except User.DoesNotExist:
            # Cases: user_info doesn't exist / phone doesn't exist / both exist, but not matched
            return Response({"message": "User matching id(or email) and phone does not exist"},
                            status=status.HTTP_404_NOT_FOUND)
        except NotAuthenticated:
            message = "not authenticated"
            return Response({"message": message}, status=status.HTTP_403_FORBIDDEN)
        except InvalidSignatureError:
            message = "Invalid access"
            return Response({"message": message}, status=status.HTTP_401_UNAUTHORIZED)
        except TimeoutException as e:
            return Response({"message": e.message}, status=e.status)


@permission_classes([IsNotAuthenticated])
class ChangePasswordAPIView(APIView):

    @transaction.atomic()
    def post(self, request):
        try:
            token_for_password_change = request.data['token_for_password_change']
            user_info_type = request.data['user_info_type']
            user_info = request.data['user_info']
            new_password = request.data['new_password']
            new_password_for_confirm = request.data['new_password_for_confirm']

            if new_password != new_password_for_confirm:
                return Response({"message": "passwords differ"}, status=status.HTTP_403_FORBIDDEN)

            user = User.objects.get(**{user_info_type: user_info})  # Exception: User.DoesNotExist

            # This token for: Authenticated phone number can try to change other's password
            if decode(token_for_password_change)['nickname'] == user.nickname + '_password_change':
                # success
                user.set_password(new_password)

                # Delete this user authentication code, for preventing re-use.
                models.AuthCode.objects.filter(phone=user.phone).delete()

                return Response({"message": "password is changed successfully"}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            message = "user information is not correct"
            return Response({"message": message}, status=status.HTTP_403_FORBIDDEN)
        except InvalidSignatureError:
            message = "Invalid access"
            return Response({"message": message}, status=status.HTTP_401_UNAUTHORIZED)


@permission_classes([IsNotAuthenticated])
class FindUsernameAPIView(APIView):

    def post(self, request):

        timeout = {'time': 5, 'unit': 'minutes'}

        try:
            phone = request.data['phone']

            # Check if authenticated before trying siging up.
            # 5 mins after authentication, it is not valid
            if not models.AuthCode.check_authenticated(phone, timeout):
                raise NotAuthenticated

            # check user
            user = User.objects.get(phone=phone) # Exception: User.DoesNotExist

            username = user.username
            masked_username = data_masking(username)

            # send email
            # send_sms(phone, 'User ID: ' + masked_username) # or send_email(phone,content) for sending email

            return Response({"message": "success",
                             "masked_username": masked_username}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"message": "User matching email and phone does not exist"},
                            status=status.HTTP_404_NOT_FOUND)
        except NotAuthenticated:
            message = "not authenticated"
            return Response({"message": message}, status=status.HTTP_403_FORBIDDEN)
