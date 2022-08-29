
from django.contrib import admin
from django.urls import path, include, re_path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from core.swagger_utils import schema_view

urlpatterns = [
    path('admin/', admin.site.urls),

    # account api app
    path('accounts/', include('accountapp.urls')),

    # Simple JWT
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Swagger
    re_path(r'swagger(?P<format>\.json|\.yaml)', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path(r'swagger', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path(r'redoc', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc-v1'),

]

# Return error type for frontend (DEBUG=FALSE)
handler404 = 'core.exception_views.error_404'
handler500 = 'core.exception_views.error_500'
