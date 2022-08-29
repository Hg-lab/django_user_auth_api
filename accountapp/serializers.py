from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from accountapp.models import User, AuthCode, PHONE_NUMBER_REGEX


class SendAuthCodeSerializer(serializers.Serializer):
    phone = serializers.CharField(validators=[PHONE_NUMBER_REGEX], max_length=11, )

    def save(self, validated_data):
        phone = self.validated_data['phone']
        auth_code = AuthCode.objects.update_or_create(
            phone=phone
        )
        return auth_code[0]



class UserModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"

    def create(self, validated_data):
        username = validated_data.get('username')
        password = validated_data.get('password')
        nickname = validated_data.get('nickname')
        first_name = validated_data.get('first_name')
        last_name = validated_data.get('last_name')
        phone = validated_data.get('phone')
        email = validated_data.get('email')

        user = User(
            username=username,
            nickname=nickname,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email
        )

        user.set_password(password)
        user.save()
        return user


class UserGettingInfoSerializer(UserModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'nickname', 'phone', ]


class AuthCodeModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthCode
        fields = "__all__"
        extra_kwargs = {
            'code': {'read_only': True},

        }

    def create(self, validated_data):
        phone = validated_data.get('phone')
        auth_code = AuthCode.objects.update_or_create(
            phone=phone
        )
        return auth_code

    def validate_phone(self, value):
        return AuthCode.check_phone_validation(self.initial_data['phone'])
    # def validate_title(self, value):
    #     """
    #     Check that the blog post is about Django.
    #     """
    #     if 'django' not in value.lower():
    #         raise serializers.ValidationError("Blog post is not about Django")
    #     return value


# Add nickname to token claim for identifying user
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['nickname'] = user.nickname
        # ...

        return token


class UnauthenticatedTokenObtainSerializer(CustomTokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        del (token['user_id'])
        # ...

        return token
