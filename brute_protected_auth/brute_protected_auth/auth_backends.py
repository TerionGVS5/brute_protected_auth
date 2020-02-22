
import redis
from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from rest_framework.authentication import BasicAuthentication
from django.utils import timezone

class BruteProtectedMixin:
    backend_type: str
    '''
    Стандартный Django использует бэкенды авторизации из AUTHENTICATION_BACKENDS
    DRF использует как DEFAULT_AUTHENTICATION_CLASSES так и AUTHENTICATION_BACKENDS
    Поэтому для стандартной Django бэкенд авторизации можно взять с backend_type
    Для DRF нужно брать тип вызвавший авторизацию - чтобы не перепутать бэкенд авторизации
    Также если user is None - то авторизация не прошла с нужным бэкендом
    '''

    def authenticate(self, request, **credentials):
        redis_conn = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
        caused_backend = getattr(request, 'caused_backend', None)
        if caused_backend is None:
            caused_backend = self.backend_type
            setattr(request, 'caused_backend', caused_backend)
        username = credentials.get('username')
        if username is not None and redis_conn.exists(f'{caused_backend}_{username}_blocked'):
            # пользователь уже заблокирован
            return None
        user = super().authenticate(request, **credentials)
        if user is None and username is not None:
            # ошибочная попытка входа, увеличиваем количество попыток и блокироем при необходимости
            key_name = f'{caused_backend}_{username}_attempts'
            now_timestamp = int(timezone.now().timestamp())
            redis_conn.lpush(key_name, now_timestamp)
            attempts_to_delete = set()
            attempts_to_check = []
            for i in range(0, redis_conn.llen(key_name)):
                curr_attempt_timestamp = int(redis_conn.lindex(key_name, i))
                if now_timestamp - settings.SECONDS_FOR_SAVE_ERROR_ATTEMPTS > curr_attempt_timestamp:
                    attempts_to_delete.add(curr_attempt_timestamp)
                elif now_timestamp - settings.SECONDS_PERIOD_FOR_CHECK_ATTEMPTS < curr_attempt_timestamp:
                    attempts_to_check.append(curr_attempt_timestamp)
            for el in attempts_to_delete:
                redis_conn.lrem(key_name, 0, el)
            if len(attempts_to_check) > settings.POSSIBLE_ERROR_ATTEMPTS:
                redis_conn.setex(f'{caused_backend}_{username}_blocked',
                                 timezone.timedelta(seconds=settings.SECONDS_FOR_BLOCK_USER), value=1)
        return user


class BasicAuthenticationProtected(BruteProtectedMixin, BasicAuthentication):
    backend_type = 'drf'


class ModelBackendProtected(BruteProtectedMixin, ModelBackend):
    backend_type = 'django'
