from django.test import TestCase

from articles.models import Article, Comment, User, UserLogin


class ArticlesTestWithSoftDelete(TestCase):
    def setUp(self):
        article1 = Article.objects.create(
            title="article 1 title",
            content="article 1 content"
        )

        comment1_for_article1 = Comment.objects.create(
            article=article1,
            text="comment1 for article1"
        )

        article2 = Article.objects.create(
            title="article 2 title",
            content="article 2 content"
        )

        comment1_for_article2 = Comment.objects.create(
            article=article2,
            text="comment1 for article2"
        )

    def test_article_delete(self):
        """
        Article should be soft deleted.
        """
        article1 = Article.objects.get(title="article 1 title")

        article1.delete()

        # Check if article1 is soft deleted in the database.
        for article in Article.objects.raw("SELECT * FROM articles_article where title='article 1 title';"):
            self.assertIsNotNone(article.deleted)
            self.assertEqual(article.title, 'article 1 title')

        # Check if query set ignores the deleted article.
        articles = Article.objects.all()
        self.assertEqual(articles.count(), 1)

        # Check if we are able to fetch deleted post by id.
        try:
            get_article1 = Article.objects.get(id=article1.id)
        except Article.DoesNotExist:
            get_article1 = None

        self.assertIsNone(get_article1)

        # Check if safe deleted objects can be accessed
        self.assertEqual(Article.objects.all_with_deleted().count(), 2)

        # We should be able to access comment using article
        comment1_for_post1 = Comment.objects.get(article__title="article 1 title")
        self.assertIsNotNone(comment1_for_post1)

    def test_get_comment_after_article_delete(self):
        """
        Should be able to retrieve the comment of a soft deleted article.
        """
        article1 = Article.objects.get(title="article 1 title")

        article1.delete()

        # We should be able to fetch the comment directly.
        comment1_for_article1 = Comment.objects.get(text="comment1 for article1")
        self.assertIsNotNone(comment1_for_article1)

        # Get the comment from related_name
        self.assertEqual(article1.article_comments.count(), 1)

    def test_comment_delete(self):
        """
        Soft delete comment.
        """
        comment1_for_post1 = Comment.objects.get(text="comment1 for article1")
        comment1_for_post1.delete()

        # Comment should not be available from get or filter
        try:
            get_comment1 = Comment.objects.get(text="comment1 for article1")
        except Comment.DoesNotExist:
            get_comment1 = None

        self.assertIsNone(get_comment1)

        # from filter.
        get_comment1_from_filter = Comment.objects.filter(text="comment1 for article1")
        self.assertEqual(get_comment1_from_filter.count(), 0)

        # Get comment from article.
        article1 = Article.objects.get(title="article 1 title")
        self.assertEqual(article1.article_comments.count(), 0)

    def test_original_objects_manager(self):
        """
        original_objects manager should fetch all the objects, including the soft deleted one's
        """
        article1 = Article.objects.get(title="article 1 title")

        article1.delete()

        self.assertEqual(Article.objects.count(), 1)
        self.assertEqual(Article.original_objects.count(), 2)


class ArticlesTestWithSoftDeleteCascade(TestCase):
    def setUp(self):
        user1 = User.objects.create(
            full_name="sam kin",
            email="sam@gm.com"
        )

        UserLogin.objects.create(
            user=user1
        )

        UserLogin.objects.create(
            user=user1
        )

    def test_soft_delete_user(self):
        """
        Delete user and check if user and its related objects are soft deleted.
        """
        user1 = User.objects.get(email="sam@gm.com")

        user1.delete()

        self.assertEqual(User.objects.count(), 0)

        # Check if user1 is soft deleted in the database.
        for user in User.objects.raw("SELECT * FROM articles_user where email='sam@gm.com';"):
            self.assertIsNotNone(user.deleted)
            self.assertEqual(user.email, 'sam@gm.com')

        # Check if user login of user user1 is soft deleted.
        self.assertEqual(UserLogin.objects.count(), 0)

        for user_login in UserLogin.objects.raw("SELECT * FROM articles_userlogin;"):
            self.assertIsNotNone(user_login.deleted)

    def test_restore_soft_deleted_user(self):
        """
        Check if restoring soft deleted user also restores its user login's.
        """
        user1 = User.objects.get(email="sam@gm.com")

        user1.delete()
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(UserLogin.objects.count(), 0)

        # Now restore the deleted user
        user1.undelete()

        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(UserLogin.objects.count(), 2)
