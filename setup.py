"""
Set up file for the django app.  A different setup file will be created for
the standalone package.
"""
from distutils.core import setup

setup(
    name="gumshoe",
    version="0.0.1",
    description="Issue tracking app based on django.",
    author="The Magnificant Nick",
    author_email="send_me_spam@yahoo.com",
    url="http://www.nickwebsite.net/gumshoe/",
    packages=["gumshoe", "gumshoe.management", "gumshoe.management.commands"]
)
