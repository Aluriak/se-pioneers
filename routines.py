"""High level routines used by main script.

"""

import os
import shutil
import gitctl
import difflib
import tempfile
from collections import Counter
from constants import LOCAL_GIT_DIR, LOCAL_GIT_DB, REMOTE_GIT_DB, DATABASE_FILE


def initialize(remote_url:str=REMOTE_GIT_DB):
    """Initialize working directory as a git repository, and retrieve the
    data from the centralized repository.

    It will only consider the database file, making a backup
    if one already exists.

    """
    if os.path.exists(DATABASE_FILE):
        shutil.move(DATABASE_FILE, DATABASE_FILE + '.bak')
        print("The database file already exists. Backup saved.")
    print("Clone Pioneers database… ", end='', flush=True)
    gitctl.clone_repository(remote_url, target=LOCAL_GIT_DIR)
    print("Done !")
    assert os.path.exists(LOCAL_GIT_DIR), "The Pioneers directory {} is not in the working directory (did the cloning succeed ?)".format(LOCAL_GIT_DIR)
    print("Install Pioneers database… ", end='', flush=True)
    shutil.copy(LOCAL_GIT_DB, DATABASE_FILE)  # TODO: maybe a symbolic link could be better ?
    print("Done !")


def missings_in_working_directory() -> [str]:
    """Yield expected directory that miss in working directory, which therefore
    do not seems to be the one expected"""
    files = frozenset(entry.name for entry in os.scandir('.'))
    expected_files = {'config', 'data', 'system', 'docs'}
    for expected_file in expected_files:
        if expected_file not in files:
            yield expected_file


def initialization_done() -> bool:
    return os.path.exists(LOCAL_GIT_DIR)


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
        if len(counts) == 1 and counts.get(' '):
            print("No modification. Nothing to do.")
            return
        else:
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


def integrate_discoveries_to_pioneers(discoveries:[str],
                                      show_discoveries:bool=False) -> bool:
    """If user modified its database while gaming (by marking systems
    as discovered, for instance), this function will retrieve and commit
    the diff on the Pioneers database.

    It will perform some sanity checks (no destruction of data, only a subset
    of the language is accepted).

    Return True if any discoveries have been commited.

    """
    discoveries = ''.join(discoveries)
    if show_discoveries and discoveries:
        print()
        print(discoveries)
        print()
    if discoveries and verified_discoveries(discoveries):
        # SpaceEngine add the last modification in the end
        # of the file, meaning that last modification is the one to keep.
        # However, in Pioneers system, it is the opposite:
        #  the first explorer is the preferred version.
        # This is implemented by adding the discoveries on top of the database file,
        #  instead of the end like SpaceEngine do.
        with tempfile.NamedTemporaryFile('w', delete=False) as fd, open(LOCAL_GIT_DB) as fref:
            fd.write(discoveries)
            fd.write(fref.read())
            # use the tempfile as local database
            tempname = fd.name
        shutil.move(tempname, LOCAL_GIT_DB)
        shutil.copy(LOCAL_GIT_DB, DATABASE_FILE)
        gitctl.commit_and_push(commit_message_from_addendum(discoveries))
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


def detect_spaceengine_pid(procname:str or iter='SpaceEngine') -> int or None or False:
    """Return the pid number of the SpaceEngine process, or None
    if no process is detected, or False if detection is not available.

    procname -- name or names to detect as SpaceEngine process

    """
    try:
        import psutil
    except ImportError:
        print("WARNING: psutil is not installed. SpaceEngine is assumed closed.")
        return False
    procnames = {procname} if isinstance(procname, str) else frozenset(procname)
    problem_encountered = True
    while problem_encountered:
        problem_encountered = False
        try:
            return next(p.pid for p in psutil.process_iter()
                        if p.name() in procnames)
        except psutil.NoSuchProcess:
            problem_encountered = True  # retry
        except StopIteration:  # no process
            return None
    return None
