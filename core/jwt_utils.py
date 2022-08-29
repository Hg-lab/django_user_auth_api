import jwt

from accountapp.serializers import UnauthenticatedTokenObtainSerializer
from core import settings


def encode_for_unauthenticated_user(user, usage_type):
    allowed_usage_types = ['password_change']

    access_token = UnauthenticatedTokenObtainSerializer.get_token(user).access_token
    decoded_payload = jwt.decode(
                    str(access_token),
                    settings.SIMPLE_JWT['SIGNING_KEY'],
                    settings.SIMPLE_JWT['ALGORITHM']
                    )

    decoded_payload['nickname'] = decoded_payload['nickname'] + '_' + str(usage_type)

    encoded_token = jwt.encode(
        decoded_payload,
        settings.SIMPLE_JWT['SIGNING_KEY'],
        settings.SIMPLE_JWT['ALGORITHM']
    )

    return encoded_token

def decode(token):
    decoded_payload = jwt.decode(
                            str(token),
                            settings.SIMPLE_JWT['SIGNING_KEY'],
                            settings.SIMPLE_JWT['ALGORITHM']
                            )

    return decoded_payload