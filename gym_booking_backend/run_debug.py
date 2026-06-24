import os
import sys
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    import django
    django.setup()
    print("Django setup succeeded!")
except Exception as e:
    print("Django setup failed with exception:")
    traceback.print_exc()
