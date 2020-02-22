from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import HttpResponse
from django.views import View


class CommonDjangoViewV1(LoginRequiredMixin, View):

    def get(self, request):
        return HttpResponse(f'Hello {request.user.username}')
