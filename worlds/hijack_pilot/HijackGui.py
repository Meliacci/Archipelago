
from ast import arg
import logging
import multiprocessing
import os
import subprocess
import shlex
import sys
from Launcher import which
from Generate import main as Gmain
from Utils import __version__,  is_linux, is_macos, is_windows

from . import HijackGenerator

if not sys.stdout:  # to make sure sm varia's "i'm working" dots don't break UT in frozen
    sys.stdout = open(os.devnull, 'w', encoding="utf-8")

logger = logging.getLogger()

DEBUG = False
ITEMS_HANDLING = 0b111
UT_MAP_TAB_KEY = "UT_MAP"

def main(*args):
    import atexit
    confirmation = atexit.register(input, "Press enter to close.")
    erargs, seed = Gmain(args=args)
    multiworld = HijackGenerator.PatchedMain(erargs, seed)
    if __debug__:
        import gc
        import sys
        import weakref
        weak = weakref.ref(multiworld)
        del multiworld
        gc.collect()  # need to collect to deref all hard references
        assert not weak(), f"MultiWorld object was not de-allocated, it's referenced {sys.getrefcount(weak())} times." \
                " This would be a memory leak."
    # in case of error-free exit should not need confirmation
    atexit.unregister(confirmation)
    print("Finalized Main")
    pass


def launch(*args):
    exe=("python","-m",__name__)
    if is_windows:
        # intentionally using a window title with a space so it gets quoted and treated as a title
        subprocess.Popen(["start", "Running Pilot Generator", *exe], shell=True)
        return
    elif is_linux:
        terminal = which('x-terminal-emulator') or which('gnome-terminal') or which('xterm')
        if terminal:
            subprocess.Popen([terminal, '-e', shlex.join(exe)])
            return
    elif is_macos:
        terminal = [which('open'), '-W', '-a', 'Terminal.app']
        subprocess.Popen([*terminal, *exe])
        return
    NuProc=multiprocessing.Process(target=main, args=args)
    NuProc.start()
    #main(args)

if __name__ == "__main__":
    main(*sys.argv[1:])
