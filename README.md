# soft-delete-options-in-django

In this repository, I try and explore different ways of doing soft delete in django, either using a library
or from the models directly.

1. Paranoia model

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
return the soft deleted objects and second, queries that return queryset will filter the softdeleted
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

Post.original_objects.all()
# Returns soft deleted objects as well, along with the undeleted ones.
```

**Note:** I've made some changes to the code found from sentry, like changing the field name `deleted_on`
 