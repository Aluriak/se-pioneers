"""High level routines about the local repository.

used database -- the cfg file used by space engine
git database -- the cfg file under git control

"""

import os
import shutil
import subprocess
from constants import LOCAL_GIT_DIR, LOCAL_GIT_DB


def synchronize():
    """Pull git database from remote and copy to used database.
    """
    #TODO: stash changes if any, or warn about it.
    os.chdir(LOCAL_GIT_DIR)
    subprocess.call(['git', 'pull'])
    os.chdir('..')


def commit_discoveries(commit_message:str):
    """Add modifications in index, commit & push them with given message"""
    # TODO: use a better tech for that. gitpython for instance.
    # TODO: handle conflicts
    os.chdir(LOCAL_GIT_DIR)
    subprocess.call(['git', 'add', DATABASE_FILENAME])
    subprocess.call(['git', 'commit', '-m', commit_message])
    subprocess.call(['git', 'push'])
    os.chdir('..')


def update_repository():
    """Will update the repository"""
    # TODO: use a better tech for that. gitpython for instance.
    # TODO: handle conflicts
    os.chdir(LOCAL_GIT_DIR)
    subprocess.call(['git', 'pull'])
    os.chdir('..')


def clone_repository(remote_url:str, target:str):
    """Will clone the repository"""
    # TODO: use a better tech for that. gitpython for instance.
    subprocess.call(['git', 'clone', remote_url, target])
