from django.http import FileResponse, Http404
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from kreo.common.permissions import IsActiveAccount

from . import services, storage
from .models import MediaAsset
from .serializers import MediaAssetSerializer, MediaUploadSerializer


class MediaUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveAccount]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        tags=["Médias"],
        summary="Téléverser un fichier (JPEG, PNG, WebP, PDF ; 10 Mo max)",
        request={"multipart/form-data": MediaUploadSerializer},
        responses={201: MediaAssetSerializer},
    )
    def post(self, request):
        ser = MediaUploadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        asset = services.create_asset(
            owner=request.user,
            uploaded_file=ser.validated_data["file"],
            alt_text=ser.validated_data["alt_text"],
            visibility=ser.validated_data["visibility"],
        )
        return Response(MediaAssetSerializer(asset).data, status=status.HTTP_201_CREATED)


class MediaDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(tags=["Médias"], summary="Supprimer un de mes fichiers", responses={204: None})
    def delete(self, request, asset_id):
        asset = MediaAsset.objects.filter(id=asset_id, owner=request.user).first()
        if asset is None:
            raise Http404
        services.delete_asset(asset)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SignedFileView(APIView):
    """Sert un fichier via URL signée (5 minutes). En prod, R2 signe directement."""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = []

    @extend_schema(exclude=True)
    def get(self, request, storage_key):
        if not storage.verify_signature(
            storage_key, request.query_params.get("expires"), request.query_params.get("sig")
        ):
            raise Http404
        try:
            handle = storage.open_file(storage_key)
        except FileNotFoundError:
            raise Http404
        response = FileResponse(handle)
        response["Cache-Control"] = "private, max-age=300"
        response["X-Content-Type-Options"] = "nosniff"
        return response
