import json
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.authtoken import views as authtoken_views

from model_mommy import mommy

from stories.serializers import Story, StorySerializer, StorySummarySerializer
from authors.serializers import Author
from api.views import StoryViewSet, StorySummaryViewSet, AuthorViewSet, create_user
# Create your tests here.

class TestStoryApi(TestCase):

    def setUp(self):
        self.story1 = mommy.make(Story, published_at=timezone.now()-timedelta(hours=1))
        self.story2 = mommy.make(Story, published_at=timezone.now())
        self.unpublished = mommy.make(Story)

    def assertValidResponse(self, request, response, data):
        expected = {
            "count": len(data),
            "next": None,
            "previous": None,
            "results": StorySerializer(instance=data, many=True,
                                       context={"request": request}).data
        }
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])

        self.assertDictEqual(expected, json.loads(response.rendered_content))

    def test_list_view(self):
        url = reverse("story-list")

        factory = APIRequestFactory()
        request = factory.get(url, format='json')
        request.user = self.story1.author.user

        view = StoryViewSet.as_view({'get': 'list'})
        response = view(request)
        response.render()

        self.assertValidResponse(request, response, [self.story2, self.story1])

    def test_list_view_by_author(self):
        url = reverse("story-list") + "?author_id=%s" % self.story1.author_id

        factory = APIRequestFactory()
        request = factory.get(url, format='json')
        request.user = self.story1.author.user

        view = StoryViewSet.as_view({'get': 'list'})
        response = view(request)
        response.render()

        self.assertValidResponse(request, response, [self.story1])

        url = reverse("story-list") + "?author_id=%s" % self.story2.author_id

        factory = APIRequestFactory()
        request = factory.get(url, format='json')
        request.user = self.story1.author.user

        view = StoryViewSet.as_view({'get': 'list'})
        response = view(request)
        response.render()

        self.assertValidResponse(request, response, [self.story2])


class TestStorySummaryApi(TestCase):
    def setUp(self):
        self.story1 = mommy.make(Story, published_at=timezone.now()-timedelta(hours=1))
        self.story2 = mommy.make(Story, published_at=timezone.now(), inspired_by_id=self.story1.id)
        self.unpublished = mommy.make(Story)

    def assertValidResponse(self, request, response, data):
        expected = {
            "count": len(data),
            "next": None,
            "previous": None,
            "results": StorySummarySerializer(instance=data, many=True,
                                       context={"request": request}).data
        }
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])

        self.assertDictEqual(expected, json.loads(response.rendered_content))

    def test_list_view(self):
        url = reverse("story-summary-list")

        factory = APIRequestFactory()
        request = factory.get(url, format='json')
        request.user = self.story1.author.user

        view = StorySummaryViewSet.as_view({'get': 'list'})
        response = view(request)
        response.render()

        self.assertValidResponse(request, response, [self.story2, self.story1])

    def test_list_view_by_author(self):
        url = reverse("story-summary-list") + "?author_id=%s" % self.story1.author_id

        factory = APIRequestFactory()
        request = factory.get(url, format='json')
        request.user = self.story1.author.user

        view = StorySummaryViewSet.as_view({'get': 'list'})
        response = view(request)
        response.render()

        self.assertValidResponse(request, response, [self.story1])

        url = reverse("story-summary-list") + "?author_id=%s" % self.story2.author_id

        factory = APIRequestFactory()
        request = factory.get(url, format='json')
        request.user = self.story1.author.user

        view = StorySummaryViewSet.as_view({'get': 'list'})
        response = view(request)
        response.render()

        self.assertValidResponse(request, response, [self.story2])

    def test_list_view_by_inspiration(self):
        url = reverse("story-summary-list") + "?inspired_by_id=%s" % self.story1.id

        factory = APIRequestFactory()
        request = factory.get(url, format='json')
        request.user = self.story1.author.user

        view = StorySummaryViewSet.as_view({'get': 'list'})
        response = view(request)
        response.render()

        self.assertValidResponse(request, response, [self.story2])

        url = reverse("story-summary-list") + "?inspired_by_id=%s" % self.story2.id

        factory = APIRequestFactory()
        request = factory.get(url, format='json')

        view = StorySummaryViewSet.as_view({'get': 'list'})
        response = view(request)
        response.render()

        self.assertValidResponse(request, response, [])


class TestUserApi(TestCase):

    def setUp(self):
        self.author = mommy.make(Author, bio_text='A Bio')
        self.author.user.set_password('PASSWORD')
        self.author.user.save()

    def test_get_token(self):

        url = reverse("api-token")

        factory = APIRequestFactory()
        request = factory.get(url, format='json')

        response = authtoken_views.obtain_auth_token(request)
        response.render()

        # Get is NOT allowed on this endpoint
        self.assertEqual(405, response.status_code)


        request = factory.post(url, {'username': self.author.user.username, 'password':'PASSWORD'}, format='json')
        response = authtoken_views.obtain_auth_token(request)
        response.render()
        self.assertEqual(200, response.status_code)
        self.assertIn('token', json.loads(response.content))


    def test_register_user(self):

        url = reverse('api-register-user')

        factory = APIRequestFactory()
        request = factory.get(url, format='json')

        response = create_user(request)
        response.render()

        # Get is NOT allowed on this endpoint
        self.assertEqual(405, response.status_code)

        request = factory.post(url, {
            'username': 'user',
            'email': 'useremail@gmail.com',
            'password': 'PASSWORD'
        }, format='json')

        response = create_user(request)
        response.render()

        # Creates
        self.assertEqual(201, response.status_code)
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(username='user')
            self.assertEqual('useremail@gmail.com', user.email)

        except UserModel.DoesNotExist:
            self.assertTrue(False, "The user was not created")


        # Try it again, it should fail
        request = factory.post(url, {
            'username': 'user',
            'email': 'useremail@gmail.com',
            'password': 'PASSWORD'
        }, format='json')

        response = create_user(request)
        response.render()

        # User already exists
        self.assertEqual(400, response.status_code)
        self.assertEqual(b'{"username":["A user with that username already exists."]}', response.content)
