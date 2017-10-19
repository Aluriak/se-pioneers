"""Gui built on top of the pioneers scripts, requesting user choice through
a tkinter gui.

"""

import os
import textwrap
import tkinter as tk
from tkinter import font
from enum import Enum

import routines
import gitctl


class State:
    """States of the program"""
    Starting = 'Starting Pioneers'
    WaitSE = 'Waiting for SpaceEngine to finish'
    Done = 'Finished !'
    DoneWithError = 'Errors !'


DEFAULT_WM_TITLE = 'floating_pioneers'

NO_COLOR = 'white'
COLOR_BG_TEXT = 'light grey'
COLOR_UNSET = 'pink'
COLOR_ERR = 'red'
COLOR_LOG = 'dark green'
COLOR_OK = 'light green'
COLOR_WAITING = '#fd6b14'

SE_STATE_AS_COLOR = {
    'running': COLOR_LOG,
    'stopped': COLOR_WAITING,
    'unknow': COLOR_ERR,
}
SE_STATES = frozenset(SE_STATE_AS_COLOR.keys())

TEXT_WIDTH, TEXT_HEIGHT = 50, 7
TEXT_AT_START = (
    '#' * TEXT_WIDTH
    + ('PIONEERS' + ' ' * (TEXT_WIDTH//2)).center(TEXT_WIDTH)
    + '#' * TEXT_WIDTH
)


class Application(tk.Frame):
    """Allow user to explore the lattice of an input context.

    Use navigation.py to implement the solver under the hood.

    """

    def __init__(self, master=None):
        master = master or tk.Tk()
        super().__init__(master)
        self.master.wm_title(DEFAULT_WM_TITLE)
        self.state = State.Starting
        self.create_widgets()

    def create_widgets(self):
        if hasattr(self, 'current_text'):
            raise NotImplementedError("create_widgets method called twice.")
        # delete existing ones
        for child in self.winfo_children():
            child.destroy()

        # text for user
        text_font = font.Font(family='TkFixedFont', size=10)
        self.current_text = tk.StringVar(value='')
        self.set_current_text(TEXT_AT_START)
        self.lab_text = tk.Label(self, textvariable=self.current_text, font=text_font, width=TEXT_WIDTH, heigh=TEXT_HEIGHT)
        self.lab_text.pack()

        # Frame containing the next two widgets
        self.middle_frame = tk.Frame(self, width=TEXT_WIDTH)
        # Next Step button
        self.str_next_step = tk.StringVar()
        self.set_str_next_step('Run')
        self.button_next = tk.Button(self.middle_frame, textvariable=self.str_next_step, width=TEXT_WIDTH//3)
        self.button_next.bind('<Button-1>', self.next_step)
        self.button_next.pack(side="right")

        # SpaceEngine state
        state_font = font.Font(family='TkFixedFont', size=10, weight='bold')
        self.str_se_state = tk.StringVar(value='')
        self.render_se_state()
        self.lab_se_state = tk.Label(self.middle_frame, width=2*TEXT_WIDTH//3,
                                     textvariable=self.str_se_state, font=state_font,
                                     fg=SE_STATE_AS_COLOR[self.se_state()])
        self.lab_se_state.pack(side="left")
        self.middle_frame.pack()

        # Logging for user
        error_font = font.Font(family='TkFixedFont', size=10, weight='bold')
        self.current_error = tk.StringVar(value=' ' * 40)
        self.lab_error = tk.Label(self, textvariable=self.current_error, fg=COLOR_ERR, font=error_font)
        self.lab_error.pack()

        # Pack all
        self.pack()


    def set_str_next_step(self, msg:str):
        """Set message shown in button"""
        self.str_next_step.set(msg.center(TEXT_WIDTH // 2))

    def set_current_text(self, msg:str):
        """Set message shown in text field"""
        text = textwrap.fill(msg.ljust(len(TEXT_AT_START)), width=TEXT_WIDTH,
                             drop_whitespace=False)
        self.current_text.set(text)

    def next_step(self, _):
        """Compute the next step, ensure user knows it"""
        new_state = None  # to be set if state change necessary
        if self.state is State.Starting:
            missing_dirs = set(routines.missings_in_working_directory())
            if missing_dirs:
                self.err("ERROR: restart needed.")
                self.set_current_text(
                    "You seems to have run the script outside of the "
                    "SpaceEngine/ install directory. That's unexpected. "
                    "You should first decide where is your SpaceEngine install folder. "
                    "I do not think it's at '{}' because directories {} are missing."
                    "".format(os.getcwd(), ', '.join(missing_dirs))
                )
                new_state = State.DoneWithError
            else:
                if not routines.initialization_done():
                    self.info("Initialization not performed. Will do…")
                    routines.initialize()
                self.info("Synchronize with remote repository…")
                gitctl.synchronize()
                self.log("Synchronization performed.")
                new_state = State.WaitSE

        elif self.state is State.WaitSE:
            if self.se_state() == 'running':
                self.button_next['background'] = COLOR_ERR
                self.err('SpaceEngine is running ! Quit it before !')
            else:
                self.info("Merge with remote database…")
                discoveries = tuple(routines.user_discoveries())
                gitctl.synchronize()
                if discoveries:
                    self.info("{} discoveries detected. They will be send.".format(len(discoveries)))
                    routines.integrate_discoveries_to_pioneers(discoveries)
                self.log("Merge performed. Thank you !")
                new_state = State.Done

        elif self.state is State.Done:
            self.quit()
        elif self.state is State.DoneWithError:
            self.quit()

        if new_state is not self.state:
            self.state = new_state
            self.render_state()


    def render_state(self):
        """Modify widgets to represent the current state"""
        self.button_next['background'] = COLOR_BG_TEXT
        if self.state is State.Starting:
            self.set_current_text('Starting Pioneers, initialize and sync…')
            self.set_str_next_step('…')
            new_state = State.WaitSE

        elif self.state is State.WaitSE:
            self.button_next['background'] = COLOR_BG_TEXT
            self.set_current_text('Start SpaceEngine. Do your discoveries.\nAfter you quit SpaceEngine, hit the button below.')
            self.set_str_next_step("I'm finished !")

        elif self.state is State.Done:
            self.button_next['background'] = COLOR_BG_TEXT
            self.set_current_text('Pioneers finished its job. You can quit !')
            self.set_str_next_step('Quit')

        elif self.state is State.DoneWithError:
            # do not modify texts ; they have been set by previous state
            self.button_next['background'] = COLOR_ERR
            self.set_str_next_step('Quit')



    def se_state(self) -> 'running' or 'stopped' or 'unknow':
        """Return the state of SpaceEngine process"""
        return {
            None: 'stopped',
            False: 'unknow'
        }.get(routines.detect_spaceengine_pid(), 'running')

    def render_se_state(self):
        self.str_se_state.set('Space Engine is ' + self.se_state())

    def err(self, msg:str):
        """Report given error message to user"""
        self.lab_error.configure(fg=COLOR_ERR)
        self.current_error.set(str(msg))
        self.update_idletasks()  # redraw (do not wait for the end of event handling)

    def log(self, msg:str):
        """Report given log message to user"""
        self.lab_error.configure(fg=COLOR_LOG)
        self.current_error.set(str(msg))
        self.update_idletasks()

    def info(self, msg:str):
        """Report given log message to user"""
        self.lab_error.configure(fg=COLOR_WAITING)
        self.current_error.set(str(msg))
        self.update_idletasks()


if __name__ == '__main__':
    gui = Application()
    gui.mainloop()
