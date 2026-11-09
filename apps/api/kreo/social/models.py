"""Fil social (V1.1) : tables présentes dans le schéma, endpoints activés par FEATURE_SOCIAL."""

from django.conf import settings
from django.db import models

from kreo.common.choices import Visibility
from kreo.common.models import UUIDPrimaryKeyModel


class Post(UUIDPrimaryKeyModel):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts"
    )
    project = models.ForeignKey(
        "projects.Project", null=True, blank=True, on_delete=models.SET_NULL, related_name="posts"
    )
    body = models.TextField(blank=True, default="")
    visibility = models.CharField(
        max_length=12, choices=Visibility.choices, default=Visibility.PUBLIC
    )
    media = models.ManyToManyField("media.MediaAsset", through="PostMedia", related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "posts"


class PostMedia(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    media = models.ForeignKey("media.MediaAsset", on_delete=models.CASCADE)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "post_media"
        constraints = [models.UniqueConstraint(fields=["post", "media"], name="uq_post_media")]


class Follow(models.Model):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following"
    )
    followed = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="followers"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "follows"
        constraints = [
            models.UniqueConstraint(fields=["follower", "followed"], name="uq_follow"),
            models.CheckConstraint(
                condition=~models.Q(follower=models.F("followed")), name="follow_not_self"
            ),
        ]


class Reaction(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    reaction = models.CharField(max_length=20, default="like")

    class Meta:
        db_table = "reactions"
        constraints = [models.UniqueConstraint(fields=["post", "user"], name="uq_reaction")]


class Comment(UUIDPrimaryKeyModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "comments"
