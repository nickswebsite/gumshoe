import os
import os.path
import shutil
import urllib
import uuid
import subprocess
import contextlib
import getpass

class Settings(object):
    INSTALL = ["nodejs", "coffeescript", "virtualenv", "ruby", "compass"]

    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    TMP_BASE = uuid.uuid4().hex
    ENV_REL = "env"
    ENV_ROOT = os.path.join(PROJECT_ROOT, ENV_REL)

    GITIGNORE_PYTHON = [
        "*.py[odc]",
    ]

    VIRTUALENV_VERSION = "1.11.4"
    VIRTUALENV_DOWNLOAD_LINK = "https://pypi.python.org/packages/source/v/virtualenv/virtualenv-{0}.tar.gz".format(VIRTUALENV_VERSION)
    VIRTUALENV_USER = "nick"
    VIRTUALENV_GROUP = "nick"
    VIRTUALENV_ARCHIVE_BASE = "virtualenv-{0}".format(VIRTUALENV_VERSION)
    VIRTUALENV_HOME = os.path.join(ENV_ROOT, ".v")

    PIP_BIN = os.path.join(VIRTUALENV_HOME, "bin/pip")
    PIP_REQUIREMENTS = os.path.join(PROJECT_ROOT, "project/requirements-cpython.txt")

    RUBY_BIN = os.path.join(ENV_ROOT, "bin/ruby")
    RUBY_GEM = os.path.join(ENV_ROOT, "bin/gem")
    RUBY_VERSION = "2.1.1"
    RUBY_ARCHIVE_ROOT = "ruby-{0}".format(RUBY_VERSION)
    RUBY_ARCHIVE_FORMAT = "tar.gz"
    RUBY_DOWNLOAD_URL = "http://cache.ruby-lang.org/pub/ruby/{0}/{1}.{2}".format(RUBY_VERSION[:-2], RUBY_ARCHIVE_ROOT, RUBY_ARCHIVE_FORMAT)

    NODEJS_VERSION = "v0.10.26"
    NODEJS_PLATFORM = "linux-x64"
    NODEJS_ARCHIVE_BASE = "node-{0}-{1}".format(NODEJS_VERSION, NODEJS_PLATFORM)
    NODEJS_ARCHIVE = "{0}.tar.gz".format(NODEJS_ARCHIVE_BASE)
    NODEJS_DOWNLOAD_URL = "http://nodejs.org/dist/{1}/{0}".format(NODEJS_ARCHIVE, NODEJS_VERSION)
    NODEJS_SYMLINK = os.path.join(ENV_ROOT, "nodejs")

settings = Settings()

GITIGNORE_TEMPLATE = """.gitignore-local

*.py[ocd]
*.tar.gz
*.gz
*.zip

build/
{envroot}
"""

class ActivateScript(object):
    def __init__(self):
        self.vars = {}
        self.paths = set()

    def set_var(self, name, value):
        self.vars[name] = value

    def add_path(self, path):
        self.paths.add(path)

    def get_text(self):
        var_lines = "\n".join(["{0}={1}".format(k, v) for k, v in self.vars.items()])
        export_lines = "\n".join(["export {0}".format(k) for k in self.vars])
        path = ":".join(list(self.paths) + ["$PATH"])
        return "\n\n".join([var_lines, export_lines, "PATH=" + path, "export PATH"])

activate_script = ActivateScript()
activate_script.add_path(os.path.join(settings.ENV_ROOT, "bin"))

@contextlib.contextmanager
def chdir(dir):
    oldcwd = os.getcwd()
    os.chdir(dir)
    yield
    os.chdir(oldcwd)

def untar(archive, cwd):
    execute(["tar", "-C", cwd, "-xzvpf", archive])

def init_gitignore(path):
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(GITIGNORE_TEMPLATE.format(
                envroot=settings.ENV_REL + "/"
            ))

def execute(cmd, fail_fast=True):
    print(cmd)
    res = subprocess.call(cmd)
    if res != 0 and fail_fast:
        raise Exception("Command railed with {0}: {1}".format(res, cmd))
    return res

def create_virtualenv(path, tmp_dir, owner=None):
    if os.path.exists(path):
        raise Exception("Path already exists")
    urllib.urlretrieve(settings.VIRTUALENV_DOWNLOAD_LINK, os.path.join(tmp_dir, "virtualenv.tar.gz"))
    execute(["tar", "-C", tmp_dir, "-xzvpf", os.path.join(tmp_dir, "virtualenv.tar.gz")])
    if owner:
        sudo = ["sudo", "-u", owner]
    else:
        sudo = []

    execute(sudo + [
        "python", os.path.join(tmp_dir, os.path.join(settings.VIRTUALENV_ARCHIVE_BASE, "virtualenv.py")), settings.VIRTUALENV_HOME
    ])

    with open(os.path.join(path, "VERSION"), "w") as f:
        f.write(settings.VIRTUALENV_VERSION)

def pip(requirements_file, user=None, sys_packages=False):
    sudo = []
    if user and user != getpass.getuser():
        sudo = ["sudo", "-u", user]

    cmd = sudo + [settings.PIP_BIN, "install", "-U", "-r", requirements_file]
    if sys_packages:
        cmd += ["--system-site-packages"]
    execute(cmd)

def create_ruby_env(tmp_dir):
    if os.path.exists(settings.RUBY_BIN):
        raise Exception("Ruby is already installed.")

    urllib.urlretrieve(settings.RUBY_DOWNLOAD_URL, os.path.join(tmp_dir, "ruby.tar.gz"))
    untar(os.path.join(tmp_dir, "ruby.tar.gz"), tmp_dir)
    with chdir(os.path.join(settings.TMP_BASE, settings.RUBY_ARCHIVE_ROOT)):
        execute(["./configure", "--prefix={0}".format(settings.ENV_ROOT)], fail_fast=True)
        execute(["make"], fail_fast=True)
        execute(["make", "install"], fail_fast=True)
    activate_script.add_path(os.path.join(settings.ENV_ROOT, "bin"))

def gem():
    execute([settings.RUBY_GEM, "update", "--system"])

def compass():
    execute([settings.RUBY_GEM, "install", "compass"])

def nodejs(tmp_dir):
    if not os.path.exists(os.path.join(settings.ENV_ROOT, settings.NODEJS_ARCHIVE_BASE)):
        urllib.urlretrieve(settings.NODEJS_DOWNLOAD_URL, os.path.join(tmp_dir, settings.NODEJS_ARCHIVE))
        untar(os.path.join(tmp_dir, settings.NODEJS_ARCHIVE), tmp_dir)
        shutil.move(os.path.join(tmp_dir, settings.NODEJS_ARCHIVE_BASE), os.path.join(settings.ENV_ROOT, settings.NODEJS_ARCHIVE_BASE))
        if os.path.exists(settings.NODEJS_SYMLINK):
            os.unlink(settings.NODEJS_SYMLINK)
        os.symlink(os.path.join(settings.ENV_ROOT, settings.NODEJS_ARCHIVE_BASE), settings.NODEJS_SYMLINK)
    activate_script.set_var("NODEJS_HOME", os.path.join(settings.ENV_ROOT, settings.NODEJS_SYMLINK))
    activate_script.add_path(os.path.join(settings.NODEJS_SYMLINK, "bin"))

def coffeescript():
    execute([os.path.join(settings.ENV_ROOT, os.path.join(settings.NODEJS_SYMLINK, "bin/npm")), "install", "-g", "coffee-script"])

if __name__ == "__main__":
    TASKS = settings.INSTALL
    try:
        os.makedirs(settings.TMP_BASE)

        if not os.path.exists:
            os.makedirs(settings.ENV_ROOT)

        if "git" in TASKS:
            if not os.path.exists(os.path.join(settings.PROJECT_ROOT, ".gitignore")):
                init_gitignore(os.path.join(settings.PROJECT_ROOT, ".gitignore"))

        project_dir = os.path.join(settings.PROJECT_ROOT, "project")
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)

        if "virtualenv" in TASKS:
            if not os.path.exists(settings.VIRTUALENV_HOME):
                create_virtualenv(settings.VIRTUALENV_HOME, settings.TMP_BASE)
            pip(settings.PIP_REQUIREMENTS, user=settings.VIRTUALENV_USER)

        if "ruby" in TASKS or "compass" in TASKS:
            if not os.path.exists(settings.RUBY_BIN):
                create_ruby_env(settings.TMP_BASE)
            gem()

            if "compass" in TASKS:
                compass()

        if "nodejs" in TASKS:
            nodejs(settings.TMP_BASE)

            if "coffeescript" in TASKS:
                coffeescript()

        with open(os.path.join(settings.ENV_ROOT, "activate.sh"), "w") as f:
            f.write(activate_script.get_text())

    finally:
        if os.path.exists(settings.TMP_BASE):
            shutil.rmtree(settings.TMP_BASE)


