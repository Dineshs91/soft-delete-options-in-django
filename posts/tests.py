from django.test import TestCase

from posts.models import Post, Comment


class PostsTest(TestCase):
    def setUp(self):
        post1 = Post.objects.create(
            title="post 1 title",
            description="post 1 description",
        )

        comment1_for_post1 = Comment.objects.create(
            text="comment1 for post1",
            post=post1
        )

        post2 = Post.objects.create(
            title="post 2 title",
            description="post 2 description"
        )

        comment1_for_post2 = Comment.objects.create(
            text="comment1 for post2",
            post=post2
        )

    def test_paranoia_post_delete(self):
        post1 = Post.objects.get(title="post 1 title")

        post1.delete()

        # Check if post1 is soft deleted in the database.
        for post in Post.objects.raw("SELECT * FROM posts_post where title='post 1 title';"):
            self.assertIsNotNone(post.deleted_on)

        # Check if query set ignores the deleted post.
        posts = Post.objects.all()
        self.assertEqual(posts.count(), 1)

        # Check if we are able to fetch deleted post by id.
        print(post1.id)
        try:
            get_post1 = Post.objects.get(id=post1.id)
        except Post.DoesNotExist:
            get_post1=None

        self.assertIsNone(get_post1)

        # Check if the deleted post can be fetched by original_objects.
        get_post1 = Post.original_objects.get(id=post1.id)
        self.assertIsNotNone(get_post1)
        self.assertIsNotNone(get_post1.deleted_on)