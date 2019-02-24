import json
from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APIRequestFactory, force_authenticate

from model_mommy import mommy

from stories.serializers import Story, StorySerializer
from api.views import StoryViewSet, AuthorViewSet

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
        