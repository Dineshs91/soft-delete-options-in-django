from django.db import models

from safedelete.models import SafeDeleteModel
from safedelete.models import SOFT_DELETE, SOFT_DELETE_CASCADE
from safedelete.managers import SafeDeleteAllManager


class Article(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE

    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    original_objects = SafeDeleteAllManager()


class Comment(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE

    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='article_comments')
    text = models.TextField()


class User(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    full_name = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class UserLogin(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_logins")
    login_time = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
