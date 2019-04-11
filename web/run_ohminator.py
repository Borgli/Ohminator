import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web.untitled.settings_ohminator")
django.setup()

import web.ohminator.ohminator
web.ohminator.ohminator.run_ohminator()
