import re
import json
from io import BytesIO
import requests
from os import path

from django.core.management.base import BaseCommand
from django.utils import timezone

from stories.models import Story
from martor.api import imgur_uploader

#import stories.wingdbstub

def get_filename(url):
    """ Remove the params (if there are any) and then remove the path to the file from the URL """
    parts = url.split('?')[0].split('/')
    return parts[-1]


def image_urls(text):
    """ Generator to pull each image from the text and yield it one at a time. Uses
          a regex to pull the image url out of the markdown """
    image_matcher = re.compile(r"\[[^\]]*\]\((?P<url>[^\)]+)\)")
    
    offset = 0
    match = image_matcher.search(text, offset)
    while match:
        url = match.groupdict()['url']
        yield url

        offset = match.end()
        match = image_matcher.search(text, offset)
        

class Command(BaseCommand):
    help = 'Reads the stories and brings all the images from wherever they are into our system (imgur)'

    def replace_image(self, url):
        """ Replace an image url with one from imgur by uploading the image to imgur """
        response = requests.get(url)
        if response.status_code == 200:
            if response.headers['content-type'].startswith('image'):
                img = BytesIO(response.content)
                img.name = get_filename(url) # martor is expecting to get the filename from here
    
                response = json.loads(imgur_uploader(img))
                if int(response["status"]) == 200:
                    return response['link']
                else:
                    self.stderr.write(json.dumps(response))
            else:
                self.stdout.write("%s is not an image" % url)
        else:
            self.stderr.write("Failed to get '%s' status_code=%s, '%s'" % (url, response.status_code, response.content))

        return None


    def handle(self, *args, **kwargs):
        
        links_modified = 0
        stories_modified = 0
        stories_checked = 0
        for story in Story.objects.published():
            
            stories_checked += 1
            replacements = {}  # Holds the old URL and the replacement (imgur URL)

            try:
                for url in image_urls(story.text):
                    if ('imgur.com' not in url and url not in replacements):
                        replacement = self.replace_image(url)
                        if replacement:
                            replacements[url] = replacement         
    
                if replacements:
                    for original, replacement in replacements.items():
                        story.text = story.text.replace(original, replacement)
                    story.save()
                    links_modified += len(replacements)
                    stories_modified += 1

            except requests.ConnectionError as xcpt:
                self.stderr.write("Failed to process an image in Story(%d): %s" % (story.id, xcpt))
                
        self.stdout.write("Checked %d stories" % stories_checked)
        self.stdout.write("Modified %d stories" % stories_modified)
        self.stdout.write("Modified %d links" % links_modified)