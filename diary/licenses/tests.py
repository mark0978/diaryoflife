from django.utils import timezone
from django.db.utils import IntegrityError
from django.urls import reverse

from django.test import TestCase, Client

from model_mommy import mommy

from licenses.models import License

# Create your tests here.

class TestLicenseModel(TestCase):
    
    def test__str__(self):
        license = mommy.make(License)
        self.assertEqual(license.name, str(license))
        
    def test_name_must_be_unique(self):
        license = mommy.make(License)
        with self.assertRaises(IntegrityError):
            mommy.make(License, name=license.name)
    
    
class TestLicenseViews(TestCase):
    
    def test_list(self):
        license1 = mommy.make(License, published_at=timezone.now())
        license2 = mommy.make(License, published_at=timezone.now())
        inactive = mommy.make(License, published_at=timezone.now(), 
                              unpublished_at=timezone.now())
        
        client = Client()
        response = client.get(reverse("licenses:list"))
        self.assertEqual(200, response.status_code)
        
        licenses = response.context.get("object_list")
        
        self.assertEqual(set([license1, license2]), set([x for x in licenses]))