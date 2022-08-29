import datetime
from random import randint

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from core.models import TimeStampedModel

# Validate Phone number field.
PHONE_NUMBER_REGEX = RegexValidator(
    regex=r'^01([0|1|6|7|8|9]?)-?([0-9]{3,4})-?([0-9]{4})$',
    message='Invalid phone number'
)


# Create your models here.
class User(AbstractUser):
    email = models.EmailField(unique=True, null=False, blank=False)

    nickname = models.CharField(max_length=50, unique=True, null=False, blank=False)
    phone = models.CharField(validators=[PHONE_NUMBER_REGEX], max_length=11, unique=True)

    REQUIRED_FIELDS = ["first_name", "last_name", "nickname", "email", "phone"]


# Create random digits to authenticate phone number
class AuthCode(TimeStampedModel):
    phone = models.CharField(validators=[PHONE_NUMBER_REGEX], primary_key=True, max_length=11)
    code = models.IntegerField()
    is_authenticated = models.BooleanField(null=False, default=False)

    class Meta:
        db_table = 'auth_code'

    def save(self, *args, **kwargs):
        self.code = randint(100000, 999999)
        super().save(*args, **kwargs)


    @classmethod
    def check_phone_validation(cls, phone):
        try:
            PHONE_NUMBER_REGEX(phone)
            return True
        except ValidationError:
            return False


    @classmethod
    def check_limit_time(cls, phone, timeout):
        time_limit = timezone.now() - datetime.timedelta(**{timeout['unit']: timeout['time']})
        result = cls.objects.filter(
            phone=phone,
            updated_at__gte=time_limit
        ).first()
        if result:
            return True
        return False

    @classmethod
    def check_authenticated(cls, phone, timeout):
        time_limit = timezone.now() - datetime.timedelta(**{timeout['unit']: timeout['time']})
        try:
            cls.objects.get(
                phone=phone,
                updated_at__gte=time_limit,
                is_authenticated=True,
            )
            return True
        except cls.DoesNotExist:
            return False