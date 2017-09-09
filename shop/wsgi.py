"""
WSGI config for shop project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""

import os
from shop import stacksampler
from django.core.wsgi import get_wsgi_application
import gevent

gevent.spawn(stacksampler.run_profiler)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shop.settings")

application = get_wsgi_application()
