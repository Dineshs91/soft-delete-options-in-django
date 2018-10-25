from __future__ import unicode_literals

from django.db import models

from db.paranoia import ParanoidModel


class Post(ParanoidModel):
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Comment(ParanoidModel):
    text = models.TextField(null=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_comments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
