from django.conf import settings
from markdown import Markdown, markdown

from martor.settings import (
    MARTOR_MARKDOWN_SAFE_MODE,
    MARTOR_MARKDOWN_EXTENSIONS,
    MARTOR_MARKDOWN_EXTENSION_CONFIGS
)

engine = None
def markdownify(text):
    """ This is a more efficient version of the markdownify.  The one from martor reinitializes all the 
          extensions with every call, this one does it once per run of the process and iff needed """
    
    global engine # Not really global, really only local to this file
    
    if not engine:
        engine = Markdown(safe_mode=MARTOR_MARKDOWN_SAFE_MODE,
                          extensions=MARTOR_MARKDOWN_EXTENSIONS,
                          extension_configs=MARTOR_MARKDOWN_EXTENSION_CONFIGS)
    else:
        engine.reset()
        
    return engine.convert(text)
