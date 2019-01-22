import os
import sys
import bjoern

for i in sys.path:
    print(i)

this_dir = os.path.dirname(os.path.abspath(__file__))

# We need the wsgi app to be able to find the settings file as easily as possible.  This
#   is as good a way as any that I've found.
sys.path.insert(0, os.path.dirname(this_dir))


from wsgi import application


bjoern.run(application, 'unix:/var/run/diary.sock')
