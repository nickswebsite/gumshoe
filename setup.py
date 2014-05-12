"""
Set up file for the django app.  A different setup file will be created for
the standalone package.
"""
#from distutils.core import setup, find_packages
from setuptools import setup, find_packages

package_data = {
                 "gumshoe": [
                     "templates/*",
                     "static/js/*",
                     "static/css/*",
                     ],
                 }

setup(
    name="gumshoe",
    version="0.0.1",
    description="Issue tracking app based on django.",
    author="The Magnificant Nick",
    author_email="send_me_spam@yahoo.com",
    url="http://www.nickwebsite.net/gumshoe/",
    packages=find_packages(),  # ["gumshoe", "gumshoe.management", "gumshoe.management.commands", "gumshoe.south_migrations", "gumshoe.standalone"],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'gumshoe=gumshoe.standalone.commands:gumshoe_manage',
            'gumshoe-init=gumshoe.standalone.commands:gumshoe_init_standalone',
        ]
    },
    install_requires=[
        'pytz',
        'Django==1.6',
        'south',
        'djangorestframework',
    ]
)
