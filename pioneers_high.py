"""An attempt to implement pioneers.py
in a much more user-friendly manner.

"""

import os
import shutil
import gitctl
import routines
import constants


TERM_WIDTH = shutil.get_terminal_size().columns


def run_pioneer_high_level_interface():
    print('#' * TERM_WIDTH)
    print(('PIONEERS' + ' ' * (TERM_WIDTH//2)).center(TERM_WIDTH))
    print('#' * TERM_WIDTH)

    spaceengine_is_running_under_pid = routines.detect_spaceengine_pid()
    if spaceengine_is_running_under_pid:
        print("ERROR: SpaceEngine is already running (pid {}). "
              "You should close it before running Pioneers."
              "".format(spaceengine_is_running_under_pid))
        exit(1)


    missing_dirs = set(routines.missings_in_working_directory())
    if missing_dirs:
        print(
            "ERROR: You seems to have run the script outside of the "
            "SpaceEngine/ install directory. That's unexpected. "
            "You should first decide where is your SpaceEngine install folder. "
            "I do not think it's at '{}' because directories {} are missing."
            "".format(os.getcwd(), ', '.join(missing_dirs))
        )
        exit(1)


    if not routines.initialization_done():
        print("Initialization not performed. Will do…")
        routines.initialize()
        print()
        print("Initialization performed.")


    print("Synchronize with remote repository…")
    gitctl.synchronize()
    print("Synchronization performed.")


    print()
    print("You can now run SpaceEngine. Hit enter key when finished.")
    input('<enter>')  # TODO: put here a real terminal, with control commands
    print()


    print("Merge with remote repository…")
    discoveries = routines.user_discoveries()
    gitctl.synchronize()
    if discoveries:
        print("{} discoveries detected. They will be send.".format(len(discoveries)))
        routines.integrate_discoveries_to_pioneers(discoveries)
    print("Merge performed.")

    print("Finished.")
    print("Thank you for using Pioneers !")


if __name__ == "__main__":
    run_pioneer_high_level_interface()
