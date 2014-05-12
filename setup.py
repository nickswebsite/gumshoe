from setuptools import setup, find_packages
import sys

def version_str(version):
    return ".".join([str(part) for part in version])

with open("CLASSIFIERS") as classifiers_file:
    CLASSIFIERS = [classifier.strip() for classifier in classifiers_file if classifier.strip()]

with open("README.md") as readme_file:
    README = readme_file.read()

with open("VERSION") as version_file:
    version = version_file.read().strip()
    VERSION = [int(part) for part in version.split(".")]

try:
    version_arg_index = sys.argv.index("--increment-version")
except ValueError:
    pass
else:
    sys.argv.pop(version_arg_index)
    VERSION[-1] += 1
    with open("VERSION", "w") as version_file:
        version_file.write(version_str(VERSION))

setup(
    name="gumshoe",
    version=version_str(VERSION),
    description="Issue tracking app based on django.",
    long_description=README,
    author="The Magnificant Nick",
    author_email="send_me_spam@yahoo.com",
    url="https://github.com/nickswebsite/gumshoe",
    packages=find_packages(),
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
    ],
    classifiers=CLASSIFIERS
)
