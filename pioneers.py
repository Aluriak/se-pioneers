#!/usr/bin/python3
"""This is a quick&dirty implementation of the behavior of Pioneers.

Usage: run it in the install directory of SpaceEngine.
See last lines for exact application sequence.

"""

import os
import re
import shutil
import difflib
import argparse
import subprocess
from collections import Counter


DATABASE_FILENAME = 'user-eng-db.cfg'
DATABASE_FILE = 'config/' + DATABASE_FILENAME
REMOTE_GIT_DB = 'https://github.com/aluriak/se-pioneers-db.git'
LOCAL_GIT_DIR = 'pioneers-db'
LOCAL_GIT_DB = os.path.join(LOCAL_GIT_DIR, DATABASE_FILENAME)
DIFFLIB_TO_HUMAN = {' ': 'unchanged', '+': 'added', '-': 'modified', '?': 'unexpected'}

REG_DATA_LOCATION = re.compile(r'LocName\s"([^"]+)"')
REG_DATA_NAME = re.compile(r'Name\s+"([^"]+)"')
REG_DATA_PIONEER = re.compile(r'Pioneer\s+"([^"]+)"')
REG_DATA_DATE = re.compile(r'Date\s+"([^"]+)"')


def cli_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--remote', type=str,
                        default=REMOTE_GIT_DB,
                        help='url to use as remote centralized database')
    # see watchdog tierce-party module
    # parser.add_argument('--watch', type=bool, action='store_true',
                        # default=False,
                        # help='Wait any modification of the database, push it immediately.')
    return parser.parse_args()


def clone_repository(remote_url:str, target:str):
    """Will clone the repository"""
    # TODO: use a better tech for that. gitpython for instance.
    subprocess.call(['git', 'clone', remote_url, target])

def update_repository():
    """Will update the repository"""
    # TODO: use a better tech for that. gitpython for instance.
    # TODO: handle conflicts
    os.chdir(LOCAL_GIT_DIR)
    subprocess.call(['git', 'pull'])
    os.chdir('..')

def commit_and_push(commit_message:str):
    # TODO: use a better tech for that. gitpython for instance.
    # TODO: handle conflicts
    update_repository()
    os.chdir(LOCAL_GIT_DIR)
    subprocess.call(['git', 'add', DATABASE_FILENAME])
    subprocess.call(['git', 'commit', '-m', commit_message])
    subprocess.call(['git', 'push'])
    os.chdir('..')


def verify_working_directory():
    """Raise error if working directory do not seems to be the one expected"""
    files = frozenset(entry.name for entry in os.scandir('.'))
    expected_files = {'config', 'data', 'system', 'docs'}
    for expected_file in expected_files:
        if expected_file not in files:
            raise EnvironmentError(
                "You seems to have run the script outside of the "
                "SpaceEngine/ install directory. That's unexpected. "
                "You should first decide where is your SpaceEngine install folder. "
                "I do not think it's at '{}' because the directory '{}' is missing."
                "".format(os.getcwd(), expected_file)
            )


def initialize(remote_url:str=REMOTE_GIT_DB):
    """Initialize working directory as a git repository, and retrieve the
    data from the centralized repository.

    It will only consider the database file, making a backup
    if one already exists.

    """
    verify_working_directory()
    if os.path.exists(LOCAL_GIT_DIR):
        print("Pioneers already have been initialized. I see that because '{}' "
              "exists. The initialization is therefore aborted."
              "".format(LOCAL_GIT_DIR))
        return
    if os.path.exists(DATABASE_FILE):
        shutil.move(DATABASE_FILE, DATABASE_FILE + '.bak')
        print("The database file already exists. Backup saved.")
    print("Clone Pioneers database… ", end='', flush=True)
    clone_repository(remote_url, target=LOCAL_GIT_DIR)
    print("Done !")
    assert os.path.exists(LOCAL_GIT_DIR), "The Pioneers directory {} is not in the working directory (did the cloning succeed ?)".format(LOCAL_GIT_DIR)
    print("Install Pioneers database… ", end='', flush=True)
    shutil.copy(LOCAL_GIT_DB, DATABASE_FILE)  # TODO: maybe a symbolic link could be better ?
    print("Done !")


def user_discoveries() -> [str]:
    """Yield the lines corresponding to user discoveries. Will indicate warnings
    if anything as been deleted."""
    print("Discoveries will be discovered…")
    comparer = difflib.Differ()
    with open(LOCAL_GIT_DB) as fref, open(DATABASE_FILE) as fnew:
        ref, new = tuple(fref), tuple(fnew)  # TODO: will not scale. Best algorithm: read line by line until one is different. Start diff then.
        comparison = comparer.compare(ref, new)
        # comparison = tuple(comparison) ; print(comparison)  # debug
        states, lines = zip(*((line[0], line) for line in comparison))
        counts = Counter(states)
        print("Modifications: " + ', '.join('{} {}'.format(v, DIFFLIB_TO_HUMAN[k]) for k, v in counts.items()))
    if counts.get('-'):
        print("Lines have been deleted. That's unexpected ! No modification is considered valid.")
    elif counts.get('+'):
        addendum = (line[2:] for line in lines if line.startswith('+ '))
        yield from addendum


def user_have_discovered_something() -> bool:
    """At least one new line (not exactly the reality, but it's enough for now)"""
    return any(user_discoveries())


def verified_discoveries(added_text:str) -> bool:
    """Run sanity checks on new lines in database. Return Falsy value
    if unexpected data."""
    # print('AYYELZ:', added_text)
    # TODO: verify fields. With a grammar, it should be easy to verify that
    #  new data is correctly formatted.
    return True


def integrate_discoveries_to_pioneers() -> bool:
    """If user modified its database while gaming (by marking systems
    as discovered, for instance), this function will retrieve and commit
    the diff on the Pioneers database.

    It will perform some sanity checks (no destruction of data, only a subset
    of the language is accepted).

    Return True if any discoveries have been commited.

    """
    update_repository()
    discoveries = ''.join(user_discoveries())
    if discoveries and verified_discoveries(discoveries):
        # commit and push
        print("Discoveries will be commited to remote repository…")
        # TODO: note that SpaceEngine add the last modification in the end
        # of the file, meaning that last modification is the one to keep.
        # However, in Pioneers system, it should be the opposite:
        #  the first explorer is the preferred version.
        # This could be implemented by a post-processing of the database file.
        shutil.copy(DATABASE_FILE, LOCAL_GIT_DB)
        commit_and_push(commit_message_from_addendum(discoveries))
        return True
    return False


def commit_message_from_addendum(added_text:str) -> str:
    """Return a commit message describing the added text"""
    # TODO: use a grammar to parse the added_text, and therefore
    #  get a way better commit messaging.
    COMMIT_MESSAGE_TEMPLATE = """
{pioneer} discovered {name} at {date}

Location: {location}
    """.strip()
    run_regex = lambda reg: reg.search(added_text).groups(0)[0]
    return COMMIT_MESSAGE_TEMPLATE.format(
        location=run_regex(REG_DATA_LOCATION),
        name=run_regex(REG_DATA_NAME),
        pioneer=run_regex(REG_DATA_PIONEER),
        date=run_regex(REG_DATA_DATE),
    )


if __name__ == "__main__":
    args = cli_args()
    # print(args)
    initialize(remote_url=args.remote)
    integrate_discoveries_to_pioneers()
