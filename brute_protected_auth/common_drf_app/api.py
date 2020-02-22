from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class CommonDRFAPIViewV1(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'result': f'Hello {request.user.username}'})
