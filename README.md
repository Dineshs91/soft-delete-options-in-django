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
 