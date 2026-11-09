from django.http import Http404
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from kreo.common.choices import Visibility
from kreo.common.permissions import IsActiveAccount
from kreo.moderation.services import is_blocked_between

from . import services
from .models import ArtistProfile
from .serializers import MyProfileSerializer, ProfileMediaOrderSerializer, PublicProfileSerializer

TAG = ["Profils"]


class PublicProfileView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(tags=TAG, summary="Profil public", responses={200: PublicProfileSerializer})
    def get(self, request, slug):
        profile = (
            ArtistProfile.objects.select_related("user", "city", "avatar")
            .prefetch_related("disciplines")
            .filter(slug=slug, user__deleted_at__isnull=True)
            .first()
        )
        if profile is None:
            raise Http404
        is_owner = request.user.is_authenticated and request.user.id == profile.user_id
        if not is_owner:
            if profile.visibility != Visibility.PUBLIC or profile.user.status != "active":
                raise Http404
            if request.user.is_authenticated and is_blocked_between(request.user, profile.user):
                raise Http404
        return Response(PublicProfileSerializer(profile, context={"request": request}).data)


class MyProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveAccount]

    @extend_schema(
        tags=TAG, summary="Mon profil (avec complétion)", responses={200: MyProfileSerializer}
    )
    def get(self, request):
        profile = services.ensure_profile(request.user)
        return Response(MyProfileSerializer(profile, context={"request": request}).data)

    @extend_schema(
        tags=TAG,
        summary="Modifier mon profil",
        request=MyProfileSerializer,
        responses={200: MyProfileSerializer},
    )
    def patch(self, request):
        profile = services.ensure_profile(request.user)
        ser = MyProfileSerializer(
            profile, data=request.data, partial=True, context={"request": request}
        )
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(MyProfileSerializer(profile, context={"request": request}).data)


class MyProfileMediaView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveAccount]

    @extend_schema(
        tags=TAG,
        summary="Définir l'ordre de ma galerie",
        request=ProfileMediaOrderSerializer,
        responses={200: MyProfileSerializer},
    )
    def post(self, request):
        profile = services.ensure_profile(request.user)
        ser = ProfileMediaOrderSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        services.set_gallery(profile, ser.validated_data["media_ids"])
        return Response(
            MyProfileSerializer(profile, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )
