from django.urls import path

from common_django_app.views import CommonDjangoViewV1

urlpatterns = [
    path('v1/common-django-view', CommonDjangoViewV1.as_view(), name='common_django_view_v1'),
]
