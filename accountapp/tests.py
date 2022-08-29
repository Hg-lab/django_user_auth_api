import datetime

import jwt
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from accountapp.models import AuthCode, User
from accountapp.serializers import CustomTokenObtainPairSerializer
from core import settings
from core.jwt_utils import decode, encode_for_unauthenticated_user


class CheckInfoExistsAPIViewTestCase(APITestCase):
    def setUp(self):
        self.mock_user = User.objects.create_user(
            username="test01",
            password="1234",
            nickname="nick01",
            first_name="한",
            last_name="현규",
            phone="01012341234",
            email="email@email.com"
        )
        self.allowed_info_types = {
            'username': 'test01',
            'nickname': 'nick01',
            'phone': '01012341234',
            'email': 'email@email.com',
        }

        self.test_url_name = reverse('check_if_exists')

    def test_check_existing(self):
        for user_info_type, user_info in self.allowed_info_types.items():
            data = {
                "user_info_type": user_info_type,
                "user_info": user_info,
            }
            response = self.client.post(self.test_url_name, data)
            self.assertEqual(response.status_code, 200)

    def test_check_if_not_existing(self):
        for user_info_type, user_info in self.allowed_info_types.items():
            data = {
                "user_info_type": user_info_type,
                "user_info": "NONEXISTENT DATA",
            }
            response = self.client.post(self.test_url_name, data)
            self.assertEqual(response.status_code, 204)

    def test_not_allowed_info_type(self):
        for user_info_type, user_info in self.allowed_info_types.items():
            data = {
                "user_info_type": "not allowed info type",
                "user_info": user_info,
            }
            response = self.client.post(self.test_url_name, data)
            self.assertEqual(response.status_code, 404)

class SendAuthCodeAPIViewTestCase(APITestCase):

    def setUp(self):
        self.mock_user = User.objects.create_user(
            username="test01",
            password="1234",
            nickname="nick01",
            first_name="한",
            last_name="현규",
            phone="01012341234",
            email="email@email.com"
        )
        self.data = {
            "auth_type": "sign-up",
            "phone": "01012345678",
        }

    def test_send_auth_code_when_sign_up(self):
        response = self.client.post(reverse('get_authentication_code'), self.data)
        self.assertEqual(response.status_code, 201)

        # Fail: Input invalid phone number
        self.data["phone"] = "111111111111"
        response = self.client.post(reverse('get_authentication_code'), self.data)
        self.assertEqual(response.status_code, 400)

    def test_send_auth_code_when_more_info_needed(self):
        data = {
            "auth_type": "find-password",
            "user_info_type": "email",
            "user_info": self.mock_user.email,
            "phone": self.mock_user.phone
        }
        response = self.client.post(reverse('get_authentication_code'), data)
        self.assertEqual(response.status_code, 201)

        # Fail: Input invalid phone number
        data["user_info"] = "fail@fail.com"
        response = self.client.post(reverse('get_authentication_code'), data)
        self.assertEqual(response.status_code, 404)


class AuthByCodeAPIViewTestCase(APITestCase):

    def setUp(self):
        self.phone = {"auth_type": "sign-up", "phone": "01012345678"}
        response = self.client.post(reverse('get_authentication_code'), self.phone)
        self.new_code = {"code": response.data['code']}

    # Success: Try authentication, right after received auth code
    def test_authenticate_by_proper_code(self):
        data = dict(self.phone, **self.new_code)
        response = self.client.post(reverse('authenticate_by_code'), data)
        self.assertEqual(response.status_code, 200)

    # Fail: Try authentication with not proper code (code + 1)
    def test_denied_by_improper_code(self):
        data = dict(self.phone, **self.new_code)
        data['code'] = str(int(data['code']) + 1)
        response = self.client.post(reverse('authenticate_by_code'), data)
        self.assertEqual(response.status_code, 400)

    def test_denied_by_invalid_phone(self):
        data = dict(self.phone, **self.new_code)
        data['phone'] = '01099999999'
        response = self.client.post(reverse('authenticate_by_code'), data)
        self.assertEqual(response.status_code, 400)

    # Fail: Try authentication at time after timeout (5 mins)
    def test_authenticate_over_limit_time(self):
        AuthCode.objects.filter(phone="01012345678").update(updated_at=timezone.now() - datetime.timedelta(minutes=5))
        data = dict(self.phone, **self.new_code)
        response = self.client.post(reverse('authenticate_by_code'), data)
        self.assertEqual(response.status_code, 408)


class SignUpAPIViewTestCase(APITestCase):
    def setUp(self):
        self.new_user = {
            "username": "test01",
            "password": "1234",
            "nickname": "nick01",
            "first_name": "한",
            "last_name": "현규",
            "phone": "01012341234",
            "email": "email@email.com"
        }
        self.mock_auth_code = AuthCode.objects.create(
            phone=self.new_user['phone'],
            code="123456",
            is_authenticated=True
        )

    # Success: After authentication by code completed
    def test_sign_up(self):
        # We already authenticated in the setUp method
        response = self.client.post(reverse('sign_up'), self.new_user)
        # self.assertIsNone(AuthCode.objects.filter(phone=self.new_user['phone']).first())
        self.assertEqual(response.status_code, 201)

    # Fail: Try signing up timeout, after 5 mins authentication
    def test_sign_up_over_timeout(self):
        # Update latest updated time(updated_at) to 5 mins before from now
        AuthCode.objects.filter(phone=self.new_user['phone']).update(
            updated_at=timezone.now() - datetime.timedelta(minutes=5))
        response = self.client.post(reverse('sign_up'), self.new_user)
        self.assertEqual(response.status_code, 403)

    # Fail: Try signing up without authentication code
    def test_sign_up_without_authentication(self):
        # Delete mock auth code data
        AuthCode.objects.filter(phone=self.new_user['phone']).delete()
        try:
            AuthCode.objects.get(pk=self.new_user['phone'])
        except ObjectDoesNotExist:
            is_deleted = True
        self.assertTrue(is_deleted)
        response = self.client.post(reverse('sign_up'), self.new_user)
        self.assertEqual(response.status_code, 403)

class SignInTestCase(APITestCase):
    class Meta:
        abstract = True

    def setUp(self):
        self.mock_user = User.objects.create_user(
            username="test01",
            password="1234",
            nickname="nick01",
            first_name="한",
            last_name="현규",
            phone="01012341234",
            email="email@email.com"
        )
        self.user_info = {
            # Need to implement. Default is id(username)
            "username": self.mock_user.username,
            "password": "1234"
        }

        # Need to implement. Default is sign in with id
        self.test_url_name = reverse('sign_in_id')

    def test_sign_in(self):
        self.response = self.client.post(self.test_url_name, self.user_info)
        if self.response.status_code == 200:
            access_token = self.response.data['access_token']
            self.decoded_payload = jwt.decode(
                access_token,
                settings.SIMPLE_JWT['SIGNING_KEY'],
                settings.SIMPLE_JWT['ALGORITHM']
            )


class SignInWithIdTestCase(SignInTestCase):

    def setUp(self):
        super().setUp()

        self.user_info = {
            "username": self.mock_user.username,
            "password": "1234"
        }

        self.test_url_name = reverse('sign_in_id')

    def test_sign_in_with_id(self):
        super().test_sign_in()
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(self.decoded_payload['nickname'], self.mock_user.nickname)

class SignInWithEmailTestCase(SignInTestCase):

    def setUp(self):
        super().setUp()

        self.user_info = {
            "email": self.mock_user.email,
            "password": "1234"
        }

        self.test_url_name = reverse('sign_in_email')

    def test_sign_in_with_email(self):
        super().test_sign_in()
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(self.decoded_payload['nickname'], self.mock_user.nickname)

    def test_sign_in_with_email_fail_email(self):
        self.user_info["email"] = "fail@fail.com"
        super().test_sign_in()
        self.assertEqual(self.response.status_code, 403)

    def test_sign_in_with_email_fail_password(self):
        self.user_info["password"] = "fail"
        super().test_sign_in()
        self.assertEqual(self.response.status_code, 403)


# User information for signing-up is id and email.
# class SignInWithPhoneTestCase(SignInTestCase):
#
#     def setUp(self):
#         super().setUp()
#
#         self.user_info = {
#             "phone": self.mock_user.phone,
#             "password": "1234"
#         }
#
#         self.test_url_name = reverse('sign_in_phone')
#
#     def test_sign_in_with_phone(self):
#         super().test_sign_in()
#         self.assertEqual(self.response.status_code, 200)
#         self.assertEqual(self.decoded_payload['nickname'], self.mock_user.nickname)


class MyAccountInformationAPIViewTestCase(APITestCase):

    def setUp(self):
        self.mock_user = User.objects.create_user(
            username="test01",
            password="1234",
            nickname="nick01",
            first_name="한",
            last_name="현규",
            phone="01012341234",
            email="email@email.com"
        )

        self.access_token = CustomTokenObtainPairSerializer.get_token(self.mock_user).access_token
        self.request_auth_header = {
            'HTTP_AUTHORIZATION':
                f'Bearer {str(self.access_token)}'
        }

    def test_get_my_information_without_token(self):
        response = self.client.get(reverse('get_my_information'))
        self.assertEqual(response.status_code, 401)

    def test_get_my_information(self):
        response = self.client.get(reverse('get_my_information'), **self.request_auth_header)
        self.assertEqual(response.status_code, 200)

    def test_get_my_information_with_manipulated_token(self):
        decode(self.access_token)['user_id'] = decode(self.access_token)['user_id'] + 1
        # Key isn't known
        manipulated_token = jwt.encode(decode(self.access_token), 'Key', settings.SIMPLE_JWT['ALGORITHM'])
        self.request_auth_header = {
            'HTTP_AUTHORIZATION':
                f'Bearer {str(manipulated_token)}'
        }
        response = self.client.get(reverse('get_my_information'), **self.request_auth_header)
        self.assertEqual(response.status_code, 401)


class FindPasswordAPIViewTestCase(APITestCase):

    def setUp(self):
        self.mock_user = User.objects.create_user(
            username="test01",
            password="1234",
            nickname="nick01",
            first_name="한",
            last_name="현규",
            phone="01012341234",
            email="email@email.com"
        )
        self.mock_auth_code = AuthCode.objects.create(
            phone=self.mock_user.phone,
            code="123456",
            is_authenticated=True
        )
        self.test_url_name = reverse('find_password')
        self.user_can_use_info = {
            'username': 'test01',
            'email': 'email@email.com'
        }

    def test_find_password(self):
        for info_type, info in self.user_can_use_info.items():
            data = {
                "user_info_type": info_type,
                "user_info": info,
                "phone": self.mock_user.phone
            }
            is_authenticated = AuthCode.objects.get(phone=data['phone'])
            self.assertTrue(is_authenticated)
            response = self.client.post(self.test_url_name, data)
            response_token = response.data['token_for_password_change']
            decoded_payload = decode(response_token)
            self.assertEqual(decoded_payload['nickname'], self.mock_user.nickname + '_password_change')
            self.assertEqual(response.status_code, 200)

    def test_find_password_now_allowed_user_info_type(self):
        for info_type, info in self.user_can_use_info.items():
            data = {
                "user_info_type": 'NOW ALLOWED USER INFO TYPE',
                "user_info": info,
                "phone": self.mock_user.phone
            }
            response = self.client.post(self.test_url_name, data)
            self.assertEqual(response.status_code, 401)

    def test_find_password_not_authenticated_phone(self):
        for info_type, info in self.user_can_use_info.items():
            data = {
                "user_info_type": info_type,
                "user_info": info,
                "phone": self.mock_user.phone
            }
            response = self.client.post(self.test_url_name, data)
            self.assertEqual(response.status_code, 403)

    def test_find_password_not_authenticated_phone(self):
        for info_type, info in self.user_can_use_info.items():
            data = {
                "user_info_type": info_type,
                "user_info": info + 'USER DOES NOT EXSIST',
                "phone": self.mock_user.phone
            }
            response = self.client.post(self.test_url_name, data)
            self.assertEqual(response.status_code, 404)

    def test_find_password_timeout(self):
        for info_type, info in self.user_can_use_info.items():
            data = {
                "user_info_type": info_type,
                "user_info": info,
                "phone": self.mock_user.phone
            }
            AuthCode.objects.filter(phone=self.mock_user.phone).update(
                updated_at=timezone.now() - datetime.timedelta(minutes=5))
            response = self.client.post(self.test_url_name, data)
            self.assertEqual(response.status_code, 403)

class ChangePasswordAPIViewTestCase(APITestCase):
    def setUp(self):
        self.mock_user = User.objects.create_user(
            username="test01",
            password="1234",
            nickname="nick01",
            first_name="한",
            last_name="현규",
            phone="01012341234",
            email="email@email.com"
        )
        self.token_for_password_change = encode_for_unauthenticated_user(self.mock_user, 'password_change')
        self.data = {
            'token_for_password_change': self.token_for_password_change,
            'user_info_type': 'username',
            'user_info': 'test01',
            'new_password': 'newpassword',
            'new_password_for_confirm': 'newpassword'
        }
        self.test_url_name = reverse('change-password')

    def test_change_password(self):
        response = self.client.post(self.test_url_name, self.data)
        self.assertIsNone(AuthCode.objects.filter(phone=self.mock_user.phone).first())
        self.assertEqual(response.status_code, 200)

    def test_change_password_user_info_invalid(self):
        data = {
            'token_for_password_change': self.token_for_password_change,
            'user_info_type': 'username',
            'user_info': 'DOES NOT EXIST',
            'new_password': 'newpassword',
            'new_password_for_confirm': 'newpassword'
        }
        response = self.client.post(self.test_url_name, data)
        self.assertIsNone(AuthCode.objects.filter(phone=self.mock_user.phone).first())
        self.assertEqual(response.status_code, 403)

    def test_change_password_deffer_passwords_exception(self):
        self.data['new_password_for_confirm'] = 'fail-password'
        response = self.client.post(self.test_url_name, self.data)
        self.assertEqual(response.status_code, 403)

    def test_change_password_token_exception(self):
        self.data[
            'token_for_password_change'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c'
        response = self.client.post(self.test_url_name, self.data)
        self.assertEqual(response.status_code, 401)


class FindUsernameAPIViewTestCase(APITestCase):

    def setUp(self):
        self.mock_user = User.objects.create_user(
            username="test01",
            password="1234",
            nickname="nick01",
            first_name="한",
            last_name="현규",
            phone="01012341234",
            email="email@email.com"
        )
        self.mock_auth_code = AuthCode.objects.create(
            phone=self.mock_user.phone,
            code="123456",
            is_authenticated=True
        )

        self.data = {
            "phone": self.mock_user.phone
        }

        self.test_url_name = reverse('find_username')

    def test_find_username(self):
        is_authenticated = AuthCode.objects.get(phone=self.data['phone']).is_authenticated
        self.assertTrue(is_authenticated)
        response = self.client.post(self.test_url_name, self.data)
        masked_username = response.data['masked_username']
        self.assertEqual(masked_username[:4], self.mock_user.username[:4])
        self.assertEqual(response.status_code, 200)

    def test_find_username_with_unauthenticated_phone(self):
        AuthCode.objects.filter(phone=self.data['phone']).update(is_authenticated=False)
        timeout = {'time': 5, 'unit': 'minutes'}
        is_authenticated = AuthCode.check_authenticated(self.data['phone'], timeout)
        self.assertFalse(is_authenticated)
        response = self.client.post(self.test_url_name, self.data)
        self.assertEqual(response.status_code, 403)

    def test_find_username_with_wrong_phone(self):
        self.data['phone'] = 'phone'
        response = self.client.post(self.test_url_name, self.data)
        self.assertEqual(response.status_code, 403)