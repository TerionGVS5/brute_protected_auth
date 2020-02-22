from django.urls import path

from common_drf_app.api import CommonDRFAPIViewV1

urlpatterns = [
    path('v1/common-drf-api-view', CommonDRFAPIViewV1.as_view(), name='common_drf_api_view_v1'),
]
