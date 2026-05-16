from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import MeSerializer


class MeView(APIView):
    def get(self, request):
        return Response(MeSerializer(request.user).data)
