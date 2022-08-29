from django.urls import path

from accountapp.views import SignUpAPIView, SendAuthCodeAPIView, AuthByCodeAPIView, SignInWithIdAPIView, \
    SignInWithEmailAPIView, SignInWithPhoneAPIView, MyAccountInformationAPIView, FindPasswordAPIView, \
    CheckInfoExistsAPIView, ChangePasswordAPIView, FindUsernameAPIView

urlpatterns = [
    path('check-if-exists/', CheckInfoExistsAPIView.as_view(), name='check_if_exists'),

    path('authentication-code/', SendAuthCodeAPIView.as_view(), name='get_authentication_code'),
    path('authenticate-by-code/', AuthByCodeAPIView.as_view(), name='authenticate_by_code'),

    path('sign-up/', SignUpAPIView.as_view(), name='sign_up'),

    path('sign-in/id/', SignInWithIdAPIView().as_view(), name='sign_in_id'),
    path('sign-in/email/', SignInWithEmailAPIView().as_view(), name='sign_in_email'),

    # User information for signing-up is id and email.
    # path('sign-in/phone/', SignInWithPhoneAPIView().as_view(), name='sign_in_phone'),

    path('my-information/', MyAccountInformationAPIView().as_view(), name='get_my_information'),

    path('find-password/', FindPasswordAPIView().as_view(), name='find_password'),
    path('change-password/', ChangePasswordAPIView().as_view(), name='change-password'),

    path('find-username/', FindUsernameAPIView().as_view(), name='find_username'),
]
