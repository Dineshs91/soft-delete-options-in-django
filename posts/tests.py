from django.test import TestCase

from posts.models import Post, Comment


class PostsTestWithParanoia(TestCase):
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
        try:
            get_post1 = Post.objects.get(id=post1.id)
        except Post.DoesNotExist:
            get_post1 = None

        self.assertIsNone(get_post1)

        # Post count should be 0.
        self.assertEqual(Post.objects.count(), 1)

        # Check if the deleted post can be fetched by original_objects.
        get_post1 = Post.original_objects.get(id=post1.id)
        self.assertIsNotNone(get_post1)
        self.assertIsNotNone(get_post1.deleted_on)

    def test_get_comment_after_post_delete(self):
        post1 = Post.objects.get(title="post 1 title")

        post1.delete()

        # We should be able to fetch the comment directly.
        comment1_for_post1 = Comment.objects.get(text="comment1 for post1")
        self.assertIsNotNone(comment1_for_post1)

        # Get the comment from related_name.
        self.assertEqual(post1.post_comments.count(), 1)

    def test_comment_delete(self):
        comment1_for_post1 = Comment.objects.get(text="comment1 for post1")
        comment1_for_post1.delete()

        # Comment should not be available from get or filter
        try:
            get_comment1 = Comment.objects.get(text="comment1 for post1")
        except Comment.DoesNotExist:
            get_comment1 = None

        self.assertIsNone(get_comment1)

        # from filter.
        get_comment1_from_filter = Comment.objects.filter(text="comment1 for post1")
        self.assertEqual(get_comment1_from_filter.count(), 0)

        # Get comment from post.
        post1 = Post.objects.get(title="post 1 title")
        self.assertEqual(post1.post_comments.count(), 0)
