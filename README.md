# soft-delete-options-in-django

In this repository, I try and explore different ways of doing soft delete in django, either using a library
or from the models directly.

The reason I am trying out all these options is to make sure that the consequences of any framework or
approach are well known before making a choice.

1. Paranoia model
2. [Django safe delete](https://github.com/makinacorpus/django-safedelete)

For all the strategies we will see how the following will work

1. Get
2. Delete
3. Queryset get and delete.
4. Relations

## Paranoia model

I found this code from [sentry](http://github.com/getsentry/sentry)

The idea here is to create a custom model manager which includes a custom queryset.

We create `ParanoiaModel`, which will serve as the base model.

```
class ParanoidModel(models.Model):
    class Meta:
        abstract = True

    deleted_on = models.DateTimeField(null=True, blank=True)

    def delete(self):
        self.deleted_on=timezone.now()
        self.save()
```

Any model which needs safe delete can inherit this base model. This works well only when an individual
object is deleted. But would fail, when delete is issued on a queryset.

So we add a custom queryset.

```
class ParanoidQuerySet(QuerySet):
    """
    Prevents objects from being hard-deleted. Instead, sets the
    ``date_deleted``, effectively soft-deleting the object.
    """

    def delete(self):
        for obj in self:
            obj.deleted_on=timezone.now()
            obj.save()


class ParanoidManager(models.Manager):
    """
    Only exposes objects that have NOT been soft-deleted.
    """

    def get_queryset(self):
        return ParanoidQuerySet(self.model, using=self._db).filter(
            deleted_on__isnull=True)
            
class ParanoidModel(models.Model):
    class Meta:
        abstract = True

    deleted_on = models.DateTimeField(null=True, blank=True)
    objects = ParanoidManager()
    original_objects = models.Manager()

    def delete(self):
        self.deleted_on=timezone.now()
        self.save()

```

We also add a custom manager. It helps us in 2 ways. We can access the original manager, which will
return the soft deleted objects and second, queries that return queryset will filter the soft deleted
objects without the need for us to specify it in each query.

Now both of the following queries work

```
class Post(ParanoidModel):
    title = models.CharField(max_length=100)
    content = models.TextField()
    
post = Post(title="soft delete strategies", content="Trying out various soft delete strategies")
post.delete()
# Will soft delete the post

Post.objects.all().delete()
# Will also soft delete all the posts.

Post.objects.get()
# Will not return any post and will raise an exception.

Post.original_objects.get()
# Will return the soft deleted post.

Post.original_objects.all()
# Returns soft deleted objects as well, along with the undeleted ones.
```

This strategy works very well for the first 3 criterion. But how does this work across relations ?

Lets add another model to the above example

```
post = Post(title="soft delete strategies", content="Trying out various soft delete strategies")

class Comment(ParanoidModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    message = models.TextField()
    
comment = Comment(post, message="Well written blog post")
# post is the object we created earlier.

post.delete()
# Soft delete the post.

print(Comment.objects.count())
# The comment of the post still exists.
```

From the above example it is clear that the soft delete is not propagated to the relations. Deleting
a post does not delete the comments related to it. They still can be accessed independently, but cannot
be accessed from the post, since the post is soft deleted.

So summarising this approach, everything works well, other than the relations handling.
This implementation is good enough, if the relation models are not queried directly. For example, once
we delete the post, the comments related to the post become relevant. Comments don't mean a thing
without its parent `post`.

The other thing to note here is, if we decide to restore a soft deleted object, we don't have to worry about its
relations, since they have not been deleted (Neither soft/hard).

**Note:** I've made some changes to the code found from sentry, like changing the field name `deleted_on`
 
 ## Django safe delete
 
 This framework provides lot of options for soft deleting. They have the following policies
 
 1. HARD_DELETE
 2. SOFT_DELETE
 3. SOFT_DELETE_CASCADE
 4. HARD_DELETE_NOCASCADE
 5. NO_DELETE
 
 Policies apply to how the delete is handled and stored in the database.
 
 They have the following visibility options
 
 1. DELETED_INVISIBLE (Default)
 2. DELETED_VISIBLE_BY_FIELD
 
 
 Visibility options apply for retrieving data.
 
 ### HARD_DELETE
 
 This is similar to the django default default behaviour, with some more options. I am not going to discuss them here.
 You can checkout their documentation [here](https://django-safedelete.readthedocs.io/en/latest/index.html).
 
 ### SOFT_DELETE
 
 This policy just soft deletes the object being deleted. The related objects remain untouched.
 
 Lets start by creating some models
 
```
from django.db import models

from safedelete.models import SafeDeleteModel
from safedelete.models import SOFT_DELETE


class Article(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE

    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Comment(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE

    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='article_comments')
    text = models.TextField()
```

Lets try out deleting an article

```
# First we create an article
article = Article.objects.create(
    title="article 1 title",
    content="article 1 content"
)

article.delete()
# Will soft delete the article.

Article.objects.all().delete()
# Will soft delete all the articles.

Article.objects.all_with_deleted()
# Will fetch all the objects including the deleting one's

Article.original_objects.all()
# Will fetch all the objects including the deleting one's using our custom manager.
```

We can restore the soft deleted object

```
article.undelete()
```

This strategy is almost similar to the paranoia design we discussed above.

### SOFT_DELETE_CASCADE

This is almost similar to the above, except that it soft delete's the related objects as well.

Let's start by creating some models

```
from django.db import models

from safedelete.models import SafeDeleteModel
from safedelete.models import SOFT_DELETE_CASCADE

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
```

Lets try deleting the user

```
user = User.objects.create(
    full_name="sam kin",
    email="sam@gm.com"
)
UserLogin.objects.create(
    user=user
)
UserLogin.objects.create(
    user=user
)

user.delete()

User.objects.count()
# User count will be 0

UserLogin.objects.count()
# UserLogin count will also be 0. (Since this is cascade soft delete)
# Both user and user login are soft deleted.
```

Here, restoring user will also restore all its login's.

```
user.undelete()
```

### NO_DELETE

This policy prevents any sort of delete soft/hard. The only way to delete is through raw sql query.
This can be useful in places where any kind of delete is not allowed from the application.
