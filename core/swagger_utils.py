from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="회원관리",
        default_version='프로젝트 버전 - 1.0',
        description="에이블리 사전 과제",
        contact=openapi.Contact(email="siregy1222@gmail.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)