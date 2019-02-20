# -*- coding: utf-8 -*-
import re
import sys
import os

from gunicorn.app.wsgiapp import run


sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
for i in sys.path:
    print(i)

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(run())