import urllib
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from rest_framework.serializers import DateTimeField as DrfDtf

from django.test import TestCase, Client
from rest_framework.test import APIRequestFactory, force_authenticate

from model_mommy import mommy

from stories.models import Story
from stories.forms import StoryForm
from stories.serializers import StorySerializer

# Create your tests here.

def clean_form(d):
    """ 2.2.x Django won't encode None as a form value, you have to convert it to an empty string
          or remove the key from the form data.  So, we change None to the empty string to behave
          like the browser. """
    for key in d.keys():
        if d[key] is None:
            d[key] = ''

    return d

class TestStoryModel(TestCase):

    def setUp(self):
        self.published0 = mommy.make(Story, text="**Published 0**",
                                     published_at=timezone.now()-timedelta(seconds=5))
        self.published1 = mommy.make(Story, text="Published 1",
                                     published_at=timezone.now()-timedelta(seconds=4))
        self.published2 = mommy.make(Story, text="**Published 2**",
                                     published_at=timezone.now(),
                                     author=self.published1.author)

        self.unpublished = mommy.make(Story, text="**UnPublished 1**", published_at=None,
                                      inspired_by=self.published1)
        self.hidden = mommy.make(Story, text="--Hidden 1--", inspired_by=self.published1,
                                 hidden_at=timezone.now())

    def test_published(self):
        stories = Story.objects.published()
        self.assertEqual(set((self.published0.id, self.published1.id, self.published2.id)),
                         set([x.id for x in stories]))
    def test_drafts(self):
        stories = Story.objects.drafts(user=self.unpublished.author.user)
        self.assertEqual(set((self.unpublished.id,)),
                         set([x.id for x in stories]))

    def test_recent(self):
        stories = Story.objects.recent()
        self.assertListEqual([self.published2.id, self.published1.id, self.published0.id],
                             [x.id for x in stories])

    def test_by_author(self):
        stories = Story.objects.by_author(author=self.published1.author)
        self.assertEqual(set((self. published1, self.published2,)),
                         set(stories))

    def test_read_time(self):
        self.assertEqual("Short read", self.published0.read_time())

    def test_html(self):
        self.assertEqual("<p><strong>Published 0</strong></p>", self.published0.html())
        self.assertEqual("<p>Published 1</p>", self.published1.html())

    def test__str__(self):
        """ Make sure the title is usable in ModelChoiceFields """
        self.assertEqual("%s: %s" % (self.published1.title, self.published1.tagline),
                         str(self.published1))

    def test_full_title(self):
        """ Make sure the full_title includes the subtitle since this is used in forms and templates """
        self.assertEqual("%s: %s" % (self.published1.title, self.published1.tagline),
                         str(self.published1))

    def test_next_chapter(self):
        """ No next chapter on a story that is not inspired_by the same author """
        self.assertIsNone(self.published1.next_chapter_id())

        chapter2 = mommy.make(Story, author=self.published1.author, preceded_by=self.published1,
                              published_at=timezone.now())
        self.published1.refresh_from_db()
        self.assertEqual(chapter2, self.published1.next_chapter())
        self.assertEqual(chapter2.id, self.published1.next_chapter_id())

        # Make sure the return value is cached so that we only query once
        self.assertNumQueries(0, self.published1.next_chapter)
        self.assertNumQueries(0, self.published1.next_chapter_id)

        # Now you see them
        self.assertTrue(hasattr(self.published1, '_next_chapter'))
        self.assertTrue(hasattr(self.published1, '_next_chapter_id'))

        # This should trigger clearing the _next_chapter* pseudo fields from the model
        self.published1.refresh_from_db()
        # Now you don't
        self.assertFalse(hasattr(self.published1, '_next_chapter'))
        self.assertFalse(hasattr(self.published1, '_next_chapter_id'))

        # And test the path where neither of these pseudo fields exist on the object when
        #   we refresh
        self.published1.refresh_from_db()


class TestStoryForm(TestCase):

    def assertFieldsConfigured(self, form):
        """ We override some field widths, make sure those are set as expected"""
        self.assertEqual(form.fields['title'].widget.attrs['size'],
                         Story._meta.get_field('title').max_length)
        self.assertEqual(form.fields['tagline'].widget.attrs['size'],
                         Story._meta.get_field('tagline').max_length)
        self.assertEqual(form.fields['text'].widget.attrs['cols'],
                         Story._meta.get_field('title').max_length)

    def test_field_setup_no_inspired_by(self):
        story = mommy.make(Story)
        form = StoryForm(user=story.author.user)

        self.assertFieldsConfigured(form)
        # Make sure the inspired_by field is NOT present
        self.assertListEqual(['author', 'title', 'tagline', 'text', 'private'],
                             list(form.fields.keys()))

        self.assertNotIn('inspired_by', form.fields)

    def test_field_setup_inspired_by(self):
        inspiration = mommy.make(Story, text='Inspiring')
        form = StoryForm(user=inspiration.author.user, initial={'inspired_by': inspiration})

        self.assertFieldsConfigured(form)
        self.assertListEqual(['author', 'title', 'tagline', 'text', 'inspired_by', 'private'],
                             list(form.fields.keys()))

    def test_field_setup_from_model(self):
        inspiration = mommy.make(Story, text='Inspiring')
        story = mommy.make(Story, text='Something', inspired_by=inspiration)
        form = StoryForm(user=story.author.user, instance=story)

        self.assertFieldsConfigured(form)
        self.assertIn('inspired_by', form.fields)


    def test_save(self):
        # If we edit an existing form, can we re-save it without change?
        story = mommy.make(Story, text='Nothing')

        form = StoryForm(user=story.author.user, instance=story)
        # This is a hack to get the data=request.POST dict for save checking
        form = StoryForm(data=form.initial, user=story.author.user, instance=story)

        saved = form.save()
        for field in Story._meta.fields:
            name = field.name
            self.assertEqual(getattr(saved, name), getattr(story, name))


        # If we create a new story with the form, does it save as expected
        form = StoryForm(data={
            'title': 'This is the title',
            'author': story.author.id,
            'text': 'This is the text',
            'inspired_by': story.id,
            'private': True
        }, user=story.author.user)
        saved = form.save()
        self.assertEqual(saved.inspired_by.id, story.id) # Should be inspired by story
        self.assertIsNone(saved.published_at)
        self.assertIsNotNone(saved.id)


        # Save a new story without an inspired_by field
        form = StoryForm(data={
            'title': 'This is the title',
            'author': story.author.id,
            'text': 'This is the text',
            'private': False
        }, user=story.author.user)
        saved = form.save()
        self.assertIsNone(saved.inspired_by) # Not inspired by anything
        self.assertIsNotNone(saved.published_at) # And published
        self.assertIsNotNone(saved.id)

    def test_save_with_no_commit(self):
        # We need a user and author so cheat and create both of these with a story
        story = mommy.make(Story, text='Nothing')
        # If we don't use commit, we should not get a new story in the DB
        form = StoryForm(data={
            'title': 'This is the title',
            'author': story.author.id,
            'text': 'This is the text',
            'private': False
        }, user=story.author.user)
        saved = form.save(commit=False)
        self.assertIsNone(saved.id)

    def test_saving_an_unpublished_story_can_set_published_at(self):
        # We need a user and author so cheat and create both of these with a story
        story = mommy.make(Story, text='Nothing', published_at=None)

        # Initially the story is not published
        self.assertIsNone(story.published_at)
        form = StoryForm(data={
            'title': 'This is the title',
            'author': story.author.id,
            'text': 'This is the text',
            'private': False  # But this should cause it to be published
        }, instance=story, user=story.author.user)
        saved = form.save()
        self.assertIsNotNone(saved.published_at)

    def test_saving_a_previously_published_story_does_not_change_the_published_at(self):
        # We need a user and author so cheat and create both of these with a story
        published_at = timezone.now() - timedelta(days=1)
        story = mommy.make(Story, text='Nothing', published_at=published_at)

        self.assertEqual(published_at, story.published_at)
        form = StoryForm(data={
            'title': 'This is the title',
            'author': story.author.id,
            'text': 'This is the text',
            'private': False  # The published_at should NOT change
        }, instance=story, user=story.author.user)
        saved = form.save()
        self.assertEqual(published_at, saved.published_at)



class TestStoryViews(TestCase):

    def setUp(self):
        self.author = mommy.make("authors.Author")
        self.author.user.set_password('PASSWORD')
        self.author.user.save()

        self.story1 = mommy.make(Story, text="Story 1",author=self.author,
                                 published_at=timezone.now()-timedelta(seconds=5))
        self.story2 = mommy.make(Story, text="Story 2", author=self.author,
                                 published_at=timezone.now()-timedelta(seconds=4))
        self.private_story = mommy.make(Story, text="Private", author=self.author,
                                        published_at=None)
        self.hidden_story = mommy.make(Story, text="Hidden", author=self.author,
                                       hidden_at=timezone.now(),
                                       published_at=timezone.now())


    def test_recent(self):
        client = Client()
        response = client.get(reverse('stories:recent'))

        stories = response.context[-1]['object_list']
        expected = [self.story2, self.story1]
        self.assertListEqual(expected, list(stories))

    def test_list_by_author(self):
        client = Client()
        response = client.get(reverse('stories:list-by-author', args=(self.author.id,)))

        stories = response.context[-1]['object_list']
        expected = [self.story2, self.story1]
        self.assertListEqual(expected, list(stories))

        # An author with a hidden story
        hidden = mommy.make(Story, text="Hidden", hidden_at=timezone.now(),
                           published_at=timezone.now())

        response = client.get(reverse('stories:list-by-author',
                                      args=(hidden.author.id,)))

        stories = response.context[-1]['object_list']
        expected = []
        self.assertListEqual(expected, list(stories))

        # An author with an unpublished story
        unpublished = mommy.make(Story, text="Hidden", published_at=None)

        response = client.get(reverse('stories:list-by-author',
                                      args=(unpublished.author.id,)))

        stories = response.context[-1]['object_list']
        expected = []
        self.assertListEqual(expected, list(stories))

    def test_create_requires_login(self):
        client = Client()

        # User NOT logged in, redirects to login
        url = reverse('stories:create')
        response = client.get(url)
        self.assertEqual(302, response.status_code)
        self.assertEqual('/accounts/signin/?next=%s' % url, response.url)

    def test_logged_in_returns_a_usable_form(self):

        # Log the user in
        client = Client()
        self.assertTrue(client.login(username=self.author.user.username, password='PASSWORD'))

        # Get the form from the server
        url = reverse('stories:create')
        response = client.get(url)
        self.assertEqual(200, response.status_code)
        form = response.context.get('form')
        self.assertFalse(form.is_bound)
        self.assertNotIn('inspired_by', form.fields) # Not present if not "inspired_by" another

    def test_create_enforces_constraints(self):

        # Log the user in
        client = Client()
        self.assertTrue(client.login(username=self.author.user.username, password='PASSWORD'))

        # Submit the form without any data (should give us some form errors)
        url = reverse('stories:create')
        response = client.post(url, data={})
        self.assertEqual(200, response.status_code)
        form = response.context.get('form')
        self.assertTrue(form.is_bound)
        self.assertDictEqual({
            'author': ['This field is required.'],
            'title': ['This field is required.'],
            'text': ['This field is required.']}, form.errors)

    def test_create_creates_story(self):

        # Log the user in
        client = Client()
        self.assertTrue(client.login(username=self.author.user.username, password='PASSWORD'))

        # Submit the form with valid data
        url = reverse('stories:create')
        response = client.get(url)
        self.assertEqual(200, response.status_code)
        form = response.context.get('form')

        form_data ={
            'title': 'This is a new title',
            'text': '**This** is the text',
            'author': list(form.fields['author'].choices)[-1][0]
        }
        response = client.post(url, data=form_data)
        self.assertEqual(302, response.status_code)
        created_story = Story.objects.get(title="This is a new title",
                                          author=self.author)

        # Which should redirect us to read the story after we have saved it.
        self.assertEqual(reverse("stories:read", args=(created_story.id,)),
                         response.url)
        self.assertIsNotNone(created_story.published_at) # Not marked as private

    def test_inspired_by_gives_you_an_inspired_by_field_and_creates_a_story(self):

        # Log the user in
        client = Client()
        self.assertTrue(client.login(username=self.author.user.username, password='PASSWORD'))

        # Now see if inspired_by works by creating a NEW story inspired by the created_story
        url = reverse('stories:create') + "?inspired_by=%s" % self.story1.id
        response = client.get(url)
        self.assertEqual(200, response.status_code)
        form = response.context.get('form')
        self.assertFalse(form.is_bound)
        self.assertIn('inspired_by', form.fields)
        self.assertEqual(form.initial['inspired_by'], self.story1)

        form_data ={
            'title': 'This is a new title',
            'text': '**This** is the text',
            'author': list(form.fields['author'].choices)[-1][0]
        }
        response = client.post(url, data=form_data)
        self.assertEqual(302, response.status_code)
        created_story = Story.objects.get(title="This is a new title",
                                          author=self.author)

        # Which should redirect us to read the story after we have saved it.
        self.assertEqual(reverse("stories:read", args=(created_story.id,)),
                         response.url)
        self.assertIsNotNone(created_story.published_at) # Not marked as private

    def test_edit_requires_login(self):
        client = Client()

        # User NOT logged in, redirects to login
        url = reverse('stories:edit', args=(self.story1.id,))
        response = client.get(url)
        self.assertEqual(302, response.status_code)
        self.assertEqual('/accounts/signin/?next=%s' % url, response.url)

    def test_the_ability_to_unpublish_a_published_story(self):

        # Log the user in
        client = Client()
        self.assertTrue(client.login(username=self.author.user.username, password='PASSWORD'))

        # And then we edit the story so we can unpublish it
        url = reverse("stories:edit", args=(self.story1.id,))
        response = client.get(url)
        self.assertEqual(200, response.status_code)
        form = response.context.get('form')

        # Now, unpublish this story and see if the published_at field is cleared
        form_data = form.initial
        form_data['private'] = 1
        response = client.post(url, data=clean_form(form_data))
        self.assertEqual(302, response.status_code)

        edited_story = Story.objects.get(title=form_data['title'], author=self.author)
        # And we redirect to the read the story page
        self.assertEqual(reverse("stories:read", args=(edited_story.id,)), response.url)

        self.assertIsNone(edited_story.published_at)


    def test_unpublishing_of_an_inspired_by_story_removes_field(self):

        # Log the user in
        client = Client()
        self.assertTrue(client.login(username=self.author.user.username, password='PASSWORD'))

        # Now see if inspired_by fails when the inspiring story is NOT published
        url = reverse('stories:create')
        response = client.get(url, data={'inspired_by': self.hidden_story.id})
        self.assertEqual(200, response.status_code)
        form = response.context.get('form')
        self.assertNotIn('inspired_by', form.fields)


    def test_read_hides_certain_stories(self):
        """ Private (unpublished) and hidden (for flagging reasons) stories are NOT readable """
        client = Client()

        response = client.get(reverse("stories:read", args=(self.private_story.id,)))
        self.assertContains(response, 'This entry is private')

        response = client.get(reverse("stories:read", args=(self.hidden_story.id,)))
        self.assertContains(response, 'This entry is hidden')

        response = client.get(reverse("stories:read", args=(self.story1.id,)))
        self.assertContains(response, self.story1.title)

    def test_new_user_gets_explanation(self):
        """ When a new user tries to create their first story, we explain pseudonyms and
              get them to create one.  After this we should take them back to story creation,
              the URL they first tried to visit before being redirected to the explainer """
        user = mommy.make(settings.AUTH_USER_MODEL)
        user.set_password('PASSWORD')
        user.save()

        client = Client()
        self.assertTrue(client.login(username=user.username, password='PASSWORD'))

        initial_url = (reverse("stories:create") + '?' + urllib.parse.urlencode({
            'inspired_by': self.story1.id
        }))

        response = client.get(initial_url, data={'inspired_by': self.story1.id})
        self.assertEqual(302, response.status_code)

        explainer_url = (reverse('authors:explain') + '?' + urllib.parse.urlencode({
            'next': initial_url
        }))
        self.assertEqual(explainer_url, response.url)

        client.get(explainer_url)
        form_data = {
            'name': 'Test Author'
        }
        response = client.post(explainer_url, data=form_data)
        self.assertEqual(302, response.status_code)
        self.assertEqual(initial_url, response.url)

    def test_next_and_previous_chapter_in_html(self):
        """ If a story has a next chapter, that story is listed on the page when you read the
              previous chapter """
        client = Client()

        self.assertIsNone(self.story1.next_chapter_id())

        # Initially this story is not inspired_by the original story
        chapter2 = mommy.make(Story, author=self.story1.author, published_at=timezone.now())
        read_chapter2_url = reverse("stories:read", args=(chapter2.id,))

        read_story1_url = reverse("stories:read", args=(self.story1.id,))
        response = client.get(read_story1_url)
        self.assertContains(response, read_chapter2_url, count=0)

        # Now we change inspired_by and it should show up as the next chapter
        chapter2.preceded_by=self.story1
        chapter2.save()

        # Make sure we don't link to it in the inspired_by list as well, it only shows up once
        response = client.get(read_story1_url)
        self.assertContains(response, read_chapter2_url, count=1)

        # And when reading chapter 2 it gives us a link to chapter 1
        response = client.get(read_chapter2_url)
        self.assertContains(response, read_story1_url, count=1)


class TestStorySerializer(TestCase):
    def test_list_serialization(self):
        """ data creation got a little crazy on this one to catch a bug.  next_chapter was not correct because
              next_chapter only works if the next_chapter has been published (not if it is still a draft)
              I added a 3rd object to catch serialization of unpublished stories
              next_chapter also requires that the author be the same for the next chapter to be found """
        story1 = mommy.make(Story, published_at=timezone.now())
        story2 = mommy.make(Story, inspired_by=story1, preceded_by=story1,
                            author=story1.author, published_at=timezone.now())
        story3 = mommy.make(Story)

        factory = APIRequestFactory()
        request = factory.get('api/stories/', format='json')
        request.user = story1.author.user

        ser = StorySerializer([story1, story2, story3], many=True, context={'request': request})

        expected = [
            {
                "id": story1.id,
                "title": story1.title,
                "tagline": "",
                "teaser": None,
                "author_id": story1.author_id,
                "html": "<p>This is a <strong>Martor</strong> field.</p>",
                "inspired_by_id": None,
                "published_at": DrfDtf().to_representation(story1.published_at),
                "preceded_by_id": None,
                "next_chapter_id": story2.id,
                "can_edit": True
            },
            {
                "id": story2.id,
                "title": story2.title,
                "tagline": "",
                "teaser": None,
                "author_id": story2.author_id,
                "html": "<p>This is a <strong>Martor</strong> field.</p>",
                "inspired_by_id": story1.id,
                "published_at": DrfDtf().to_representation(story2.published_at),
                "preceded_by_id": story1.id,
                "next_chapter_id": None,
                "can_edit": True
            },
            {
                "id": story3.id,
                "title": story3.title,
                "tagline": "",
                "teaser": None,
                "author_id": story3.author_id,
                "html": "<p>This is a <strong>Martor</strong> field.</p>",
                "inspired_by_id": None,
                "published_at": None,
                "preceded_by_id": None,
                "next_chapter_id": None,
                "can_edit": False
            }
        ]
        self.maxDiff = None
        self.assertDictEqual(expected[0], ser.data[0])
        self.assertDictEqual(expected[1], ser.data[1])
        self.assertDictEqual(expected[2], ser.data[2])
        self.assertEqual(expected, ser.data)

