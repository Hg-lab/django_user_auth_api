from drf_yasg import openapi

swagger_params = {
    'get_params_CheckInfoExistsAPIView':openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user_info_type': openapi.Schema(default='email', type=openapi.TYPE_STRING, description='username, nickname, phone, email'),
                'user_info': openapi.Schema(default='email@email', type=openapi.TYPE_STRING, description='중복체크할 사용자 정보'),
            }
        ),

    'get_params_SendAuthCodeAPIView': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'auth_type': openapi.Schema(default='sign-up',
                                        description='sign-up, find-password',
                                        type=openapi.TYPE_STRING,),
            'phone': openapi.Schema(default='01012341234',
                                        description='휴대폰번호',
                                        type=openapi.TYPE_STRING, ),
            'user_info_type': openapi.Schema(default='username',required=[False],
                                    description='사용자 정보 필드',
                                    type=openapi.TYPE_STRING, ),
            'user_info': openapi.Schema(default='test01',required=[False],
                                    description='사용자 정보',
                                    type=openapi.TYPE_STRING, ),
        }
    ),

    'get_params_AuthByCodeAPIView': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'phone': openapi.Schema(default='01012341234',
                                        description='휴대폰번호',
                                        type=openapi.TYPE_STRING, ),
            'code': openapi.Schema(default='123456',
                                    description='인증번호',
                                    type=openapi.TYPE_STRING, ),
        }
    ),
    'get_params_SignUpAPIView': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'username': openapi.Schema(default='sign-up',
                                        description='아이디',
                                        type=openapi.TYPE_STRING,),
            'password': openapi.Schema(default='1234',
                                        description='비밀번호',
                                        type=openapi.TYPE_STRING, ),
            'nickname': openapi.Schema(default='nick01',
                                    description='닉네임',
                                    type=openapi.TYPE_STRING, ),
            'first_name': openapi.Schema(default='현규',
                                    description='이름(성)',
                                    type=openapi.TYPE_STRING, ),
            'last_name': openapi.Schema(default='한',
                                         description='이름(이름)',
                                         type=openapi.TYPE_STRING, ),
            'phone': openapi.Schema(default='01012341234',
                                         description='휴대폰 번호',
                                         type=openapi.TYPE_STRING, ),
            'email': openapi.Schema(default='email@email.com',
                                         description='이메일',
                                         type=openapi.TYPE_STRING, ),
        }
    ),
    'get_params_SignInWithIdAPIView': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'username': openapi.Schema(default='sign-up',
                                       description='아이디',
                                       type=openapi.TYPE_STRING, ),
            'password': openapi.Schema(default='01012341234',
                                       description='비밀번호',
                                       type=openapi.TYPE_STRING, ),
        },
    ),
    'get_params_SignInWithEmailAPIView': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'email': openapi.Schema(default='email@email.com',
                                         description='이메일',
                                         type=openapi.TYPE_STRING, ),
            'password': openapi.Schema(default='01012341234',
                                       description='비밀번호',
                                       type=openapi.TYPE_STRING, ),
        }
    ),
    'get_params_SignInWithPhoneAPIView': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'phone': openapi.Schema(default='01012341234',
                                         description='휴대폰 번호',
                                         type=openapi.TYPE_STRING, ),
            'password': openapi.Schema(default='01012341234',
                                       description='비밀번호',
                                       type=openapi.TYPE_STRING, ),
        }
    ),
    'get_params_FindPasswordAPIView': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user_info_type': openapi.Schema(default='username',required=[False],
                                    description='사용자 정보 필드',
                                    type=openapi.TYPE_STRING, ),
            'user_info': openapi.Schema(default='test01',required=[False],
                                    description='사용자 정보',
                                    type=openapi.TYPE_STRING, ),
            'phone': openapi.Schema(default='01012341234',
                                         description='휴대폰 번호',
                                         type=openapi.TYPE_STRING, ),
        }
    ),
    'get_params_MyAccountInformationAPIView': [
            openapi.Parameter(
                'HTTP_AUTHORIZATION Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c',
                openapi.IN_HEADER,
                type=openapi.TYPE_STRING,
                description='API 키: 헤더에 Authorization Bearer {API Key} 형태로 전달'
            )
        ],

}

