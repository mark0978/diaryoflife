from io import StringIO
from itertools import zip_longest

from requests import ConnectionError

from django.utils import timezone
from django.test import TestCase
import responses
from model_mommy import mommy

from stories.models import Story
from .commands.fix_image_links import get_filename, image_urls, Command as FixImageLinksCommand
from .commands.create_sample_stories import Command as CreateSampleStoriesCommand


class TestUtilFunctions(TestCase):
    def test_get_filename(self):
        url = "http://www.gutenberg.org/files/18155/18155-h/images/imgplate-3.jpg"
        self.assertEqual("imgplate-3.jpg", get_filename(url))
        url += "?action=v&size=large"
        self.assertEqual("imgplate-3.jpg", get_filename(url))


    def test_img_urls(self):
        text = """The second Pig met a Man with a bundle of furze, and said, "Please, Man, give me that furze to build a house"; which the Man did, and the Pig built his house.
![Then along came the Wolf](http://www.gutenberg.org/files/18155/18155-h/images/img004.jpg)
Then along came the Wolf and said, "Little Pig, little Pig, let me come in."
"No, no, by the hair of my chinny chin chin."
"Then I'll puff and I'll huff, and I'll blow your house in!" So he huffed and he puffed, and he puffed and he huffed, and at last he blew the house down, and ate up the second little Pig.
![The wolf](http://www.gutenberg.org/files/18155/18155-h/images/img005.jpg)"""

        expected_urls = ('http://www.gutenberg.org/files/18155/18155-h/images/img004.jpg',
                         'http://www.gutenberg.org/files/18155/18155-h/images/img005.jpg')

        # Use zip_longest so we make sure we get all the expected URLs and don't miss out if
        #  expected_urls is too short
        for expected, actual in zip_longest(expected_urls, image_urls(text)):
            self.assertEqual(expected, actual)

class TestFixImageLinksCommand(TestCase):

    def setUp(self):
        self.stdout = StringIO()
        self.stderr = StringIO()
        self.cmd = FixImageLinksCommand(stdout=self.stdout, stderr=self.stderr, no_color=True)

    def assertStdOutput(self, expected):
        """ The command output the specified expected text to stderr, empty string for no output """
        self.stdout.seek(0)
        self.assertEqual(expected, self.stdout.read())

    def assertStdError(self, expected):
        """ The command output the specified expected text to stderr, empty string for no output """
        self.stderr.seek(0)
        self.assertEqual(expected, self.stderr.read())

    @responses.activate
    def test_connection_error(self):
        with self.assertRaises(ConnectionError):
            self.cmd.replace_image('http://www.gutenberg.org/files/18155/18155-h/images/img004.jpg')

    @responses.activate
    def test_replace_image_404(self):
        """ If we can't get the original image, we won't try to replace it..."""
        responses.add(responses.GET, 'http://www.gutenberg.org/files/18155/18155-h/images/img004.jpg',
                      body="Not Found", status=404)

        self.assertEqual(None,
                         self.cmd.replace_image('http://www.gutenberg.org/files/18155/18155-h/images/img004.jpg'))
        self.assertStdOutput('')
        self.assertStdError("Failed to get 'http://www.gutenberg.org/files/18155/18155-h/images/img004.jpg' status_code=404, 'b'Not Found''\n")

    @responses.activate
    def test_replace_image_works(self):
        # This is the response for downloading the image
        responses.add(responses.GET, 'http://www.gutenberg.org/files/18155/18155-h/images/img004.jpg',
                      body="This is the image", status=200, content_type='image/jpeg')
        # And this is the response for uploading the image via the martor.image_uploader
        respdata = {
            "status": 200,
            "data": {
                "link": "https://i.imgur.com/pViGEMi.jpg",
                "name": "img006.jpg"
            }
        }
        responses.add(responses.POST, 'https://api.imgur.com/3/upload.json',
                      json=respdata, status=200)

        self.assertEqual('https://i.imgur.com/pViGEMi.jpg',
                         self.cmd.replace_image('http://www.gutenberg.org/files/18155/18155-h/images/img004.jpg'))
        self.assertStdOutput('')
        self.assertStdError('')

    @responses.activate
    def test_not_an_image(self):
        # This is the response for downloading the image
        responses.add(responses.GET, 'http://www.gutenberg.org/files/18155/18155-h/images/img004.jpg',
                      body="This is NOT an image", status=200, content_type='text/html')

        self.assertEqual(None,
                         self.cmd.replace_image('http://www.gutenberg.org/files/18155/18155-h/images/img004.jpg'))
        self.assertStdOutput('http://www.gutenberg.org/files/18155/18155-h/images/img004.jpg is not an image\n')
        self.assertStdError('')

    @responses.activate
    def test_cannot_upload_image(self):
        # This is the response for downloading the image
        responses.add(responses.GET, 'http://www.gutenberg.org/files/18155/18155-h/images/img004.jpg',
                      body="This is NOT an image", status=200, content_type='text/html')

        self.assertEqual(None,
                         self.cmd.replace_image('http://www.gutenberg.org/files/18155/18155-h/images/img004.jpg'))
        self.assertStdOutput('http://www.gutenberg.org/files/18155/18155-h/images/img004.jpg is not an image\n')
        self.assertStdError('')

    @responses.activate
    def test_replace_image_disallowed(self):
        # This is the response for downloading the image
        responses.add(responses.GET, 'http://www.gutenberg.org/files/18155/18155-h/images/img004.jpg',
                      body="This is the image", status=200, content_type='image/jpeg')
        # And this is the response for uploading the image via the martor.image_uploader
        respdata = {
            "status": 403,
            "error": "Permission denied"
        }
        responses.add(responses.POST, 'https://api.imgur.com/3/upload.json',
                      json=respdata, status=403)

        self.assertEqual(None,
                         self.cmd.replace_image('http://www.gutenberg.org/files/18155/18155-h/images/img004.jpg'))
        self.assertStdOutput('')
        # This looks wrong to me, but it stems from the way martor.image_uploadeer is written (which I think is broken)
        #   It encodes the entirety of the error response as the value for the error which ends up with all the \\
        #   crap that doesn't belong here.....
        self.assertStdError('{"status": 403, "error": "{\\"status\\": 403, \\"error\\": \\"Permission denied\\"}"}\n')

    @responses.activate
    def test_cmd_handle(self):
        text = """The second Pig met a Man with a bundle of furze, and said, "Please, Man, give me that furze to build a house"; which the Man did, and the Pig built his house.
![Then along came the Wolf](http://www.gutenberg.org/files/18155/18155-h/images/img004.jpg)
Then along came the Wolf and said, "Little Pig, little Pig, let me come in."
"No, no, by the hair of my chinny chin chin."
"Then I'll puff and I'll huff, and I'll blow your house in!" So he huffed and he puffed, and he puffed and he huffed, and at last he blew the house down, and ate up the second little Pig.
![The wolf](http://www.gutenberg.org/files/18155/18155-h/images/img005.jpg)"""

        story = mommy.make(Story, text=text, published_at=timezone.now())

        # This is the response for downloading the 2 images
        responses.add(responses.GET, 'http://www.gutenberg.org/files/18155/18155-h/images/img004.jpg',
                      body="This is the image", status=200, content_type='image/jpeg')

        responses.add(responses.GET, 'http://www.gutenberg.org/files/18155/18155-h/images/img005.jpg',
                      body="This is the image", status=200, content_type='image/jpeg')

        # And these are the responses for uploading the image via the martor.image_uploader
        respdata = {
            "status": 200,
            "data": {
                "link": "https://i.imgur.com/first.jpg",
                "name": "img006.jpg"
            }
        }
        responses.add(responses.POST, 'https://api.imgur.com/3/upload.json', json=respdata, status=200)

        respdata = {
            "status": 200,
            "data": {
                "link": "https://i.imgur.com/second.jpg",
                "name": "img006.jpg"
            }
        }
        responses.add(responses.POST, 'https://api.imgur.com/3/upload.json', json=respdata, status=200)

        self.cmd.handle()
        self.assertStdOutput('Checked 1 stories\nModified 1 stories\nModified 2 links\n')
        self.assertStdError('')

        story = Story.objects.get(pk=story.id)

        expected = """The second Pig met a Man with a bundle of furze, and said, "Please, Man, give me that furze to build a house"; which the Man did, and the Pig built his house.
![Then along came the Wolf](https://i.imgur.com/first.jpg)
Then along came the Wolf and said, "Little Pig, little Pig, let me come in."
"No, no, by the hair of my chinny chin chin."
"Then I'll puff and I'll huff, and I'll blow your house in!" So he huffed and he puffed, and he puffed and he huffed, and at last he blew the house down, and ate up the second little Pig.
![The wolf](https://i.imgur.com/second.jpg)"""
        self.assertEqual(expected, story.text)

    def test_cmd_handle_nothing_to_convert(self):
        text = """This is a test which has nothing to convert"""

        story = mommy.make(Story, text=text, published_at=timezone.now())

        self.cmd.handle()
        self.assertStdOutput('Checked 1 stories\nModified 0 stories\nModified 0 links\n')
        self.assertStdError('')

        story = Story.objects.get(pk=story.id)

        expected = text
        self.assertEqual(expected, story.text)

    def test_cmd_handle_already_imgur_urls(self):
        text = """This already has an imgur url  ![Then along came the Wolf](https://i.imgur.com/first.jpg)"""

        story = mommy.make(Story, text=text, published_at=timezone.now())

        self.cmd.handle()
        self.assertStdOutput('Checked 1 stories\nModified 0 stories\nModified 0 links\n')
        self.assertStdError('')

        story = Story.objects.get(pk=story.id)

        expected = text
        self.assertEqual(expected, story.text)

    @responses.activate
    def test_cmd_handle_cant_read_source_image(self):
        text = """This image url is broken and will fail  ![Then along came the Wolf](https://example.com/first.jpg)"""

        story = mommy.make(Story, text=text, published_at=timezone.now())

        self.cmd.handle()
        self.assertStdOutput('Checked 1 stories\nModified 0 stories\nModified 0 links\n')
        self.assertStdError('Failed to process an image in Story(%d): Connection refused: GET https://example.com/first.jpg\n' % story.id)

        story = Story.objects.get(pk=story.id)

        expected = text
        self.assertEqual(expected, story.text)

    @responses.activate
    def test_cmd_handle_cant_upload_to_imgur(self):
        text = """IMGUR will refuse to accept this image ![Then along came the Wolf](https://example.com/first.jpg)"""

        story = mommy.make(Story, text=text, published_at=timezone.now())

        responses.add(responses.GET, 'https://example.com/first.jpg',
                      body="This is the image", status=200, content_type='image/jpeg')

        # And these are the responses for uploading the image via the martor.image_uploader
        respdata = {
            "status": 403,
            "error": "Not allowed"
        }
        responses.add(responses.POST, 'https://api.imgur.com/3/upload.json', json=respdata, status=403)

        self.cmd.handle()
        self.assertStdOutput('Checked 1 stories\nModified 0 stories\nModified 0 links\n')
        self.assertStdError('{"status": 403, "error": "{\\"status\\": 403, \\"error\\": \\"Not allowed\\"}"}\n')

        story = Story.objects.get(pk=story.id)

        expected = text
        self.assertEqual(expected, story.text)

    @responses.activate
    def test_cmd_handle_cant_download_source(self):
        text = """IMGUR will refuse to accept this image ![Then along came the Wolf](https://example.com/first.jpg)"""

        story = mommy.make(Story, text=text, published_at=timezone.now())

        responses.add(responses.GET, 'https://example.com/first.jpg',
                      body="Not Found", status=404, content_type='image/jpeg')

        self.cmd.handle()
        self.assertStdOutput('Checked 1 stories\nModified 0 stories\nModified 0 links\n')
        self.assertStdError("Failed to get 'https://example.com/first.jpg' status_code=404, 'b'Not Found''\n")

        story = Story.objects.get(pk=story.id)

        expected = text
        self.assertEqual(expected, story.text)

class TestCreateSampleStories(TestCase):

    def setUp(self):
        self.stdout = StringIO()
        self.stderr = StringIO()
        self.cmd = CreateSampleStoriesCommand(stdout=self.stdout, stderr=self.stderr, no_color=True)

    def test_normal_run(self):

        self.cmd.handle()

        chapter3 = Story.objects.published(title="A story in 3 parts", tagline="Chapter 3").get()
        chapter2 = chapter3.preceded_by
        chapter1 = chapter2.preceded_by
        self.assertIsNone(chapter1.preceded_by)

        inspiring = Story.objects.published(title="A very inspiring story", tagline="Oh what a joy!").get()
        self.assertEqual(7, Story.objects.inspired(inspiring).count())
