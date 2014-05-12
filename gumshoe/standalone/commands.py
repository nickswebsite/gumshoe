#!python
import os
import sys

def gumshoe_manage():
    cwd = os.getcwd()
    sys.path.insert(0, cwd)

    if "test" in sys.argv:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gumshoe.standalone.settings_test")
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gumshoe.standalone.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)

def gumshoe_init_standalone():
    config_dir = "conf"
    if not os.path.exists(config_dir):
        os.mkdir(config_dir)
    with open(os.path.join(config_dir, "__init__.py"), "a"):
        pass
    with open(os.path.join(config_dir, "settings.py"), "w") as f:
        f.write("""from gumshoe.standalone.settings import *
""")

