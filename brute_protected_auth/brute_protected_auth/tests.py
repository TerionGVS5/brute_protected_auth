from unittest import mock

import redis
import base64

from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED

from django.conf import settings


class BruteProtectedTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        User.objects.create_user('test_user', 'test_user@gmail.com', 'test_password')
        cls.redis_conn = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
        cls.drf_protected_url = reverse('common_drf_api_view_v1')
        cls.django_login_url = reverse('login')

    def setUp(self):
        super().setUp()
        self.redis_conn.flushdb()

    def set_ok_basic_auth(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Basic {base64.b64encode("test_user:test_password".encode()).decode()}')

    def set_bad_basic_auth(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Basic {base64.b64encode("test_user:incorrect".encode()).decode()}')

    def test_drf_only_ok(self):
        self.drf_ok_login()

    def test_drf_only_error(self):
        self.drf_error_login()

    def test_drf_possible_error_then_ok(self):
        for _ in range(settings.POSSIBLE_ERROR_ATTEMPTS):
            self.drf_error_login()
        self.drf_ok_login()

    def test_drf_block_simulate_wait_then_ok(self):
        self.drf_block()
        for key in self.redis_conn.scan_iter('*_blocked'):
            ttl_for_blocked = self.redis_conn.ttl(key)
            if ttl_for_blocked <= settings.SECONDS_FOR_BLOCK_USER:
                self.redis_conn.delete(key)
        self.drf_ok_login()

    def test_django_only_ok(self):
        self.django_ok_login()

    def test_django_only_error(self):
        self.django_error_login()

    def test_django_possible_error_then_ok(self):
        for _ in range(settings.POSSIBLE_ERROR_ATTEMPTS):
            self.django_error_login()
        self.django_ok_login()

    def test_drf_block_but_django_ok(self):
        self.drf_block()
        self.django_ok_login()

    def test_django_block_but_drf_ok(self):
        self.django_block()
        self.drf_ok_login()

    def test_django_block_and_drf_block(self):
        self.django_block()
        self.drf_block()

    def drf_block(self):
        now = timezone.now()
        for _ in range(settings.POSSIBLE_ERROR_ATTEMPTS):
            self.drf_error_login()
        with mock.patch.object(timezone, 'now', return_value=now):
            self.drf_error_login()
        self.drf_blocked_login()

    def drf_ok_login(self):
        self.set_ok_basic_auth()
        response = self.client.get(self.drf_protected_url)
        self.assertEqual(response.status_code, HTTP_200_OK)

    def drf_blocked_login(self):
        self.set_ok_basic_auth()
        response = self.client.get(self.drf_protected_url)
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def drf_error_login(self):
        self.set_bad_basic_auth()
        response = self.client.get(self.drf_protected_url)
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def django_error_login(self):
        response = self.client.post(self.django_login_url, {'username': 'test_user',
                                                            'password': 'incorrect'}, follow=True)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertNotEqual(response.content.decode('utf-8'), 'Hello test_user')

    def django_ok_login(self):
        response = self.client.post(self.django_login_url, {'username': 'test_user',
                                                            'password': 'test_password'}, follow=True)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.content.decode('utf-8'), 'Hello test_user')

    def django_blocked_login(self):
        response = self.client.post(self.django_login_url, {'username': 'test_user',
                                                            'password': 'test_password'}, follow=True)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertNotEqual(response.content.decode('utf-8'), 'Hello test_user')

    def django_block(self):
        now = timezone.now()
        for _ in range(settings.POSSIBLE_ERROR_ATTEMPTS):
            self.django_error_login()
        with mock.patch.object(timezone, 'now', return_value=now):
            self.django_error_login()
        self.django_blocked_login()
