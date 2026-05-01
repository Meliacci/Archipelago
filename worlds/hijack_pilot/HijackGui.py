
import logging
import os
import sys

import Generate
from Utils import __version__

try:
    from Utils import gui_enabled
except ImportError:
    gui_enabled = not sys.stdout or "--nogui" not in sys.argv #if we fail to find, just guess it ourselves

from Generate import main as GMain, mystery_argparse
from . import HIJACK_VERSION, HijackGenerator

if not sys.stdout:  # to make sure sm varia's "i'm working" dots don't break UT in frozen
    sys.stdout = open(os.devnull, 'w', encoding="utf-8")  # from https://stackoverflow.com/a/6735958

logger = logging.getLogger("Generator")

DEBUG = False
ITEMS_HANDLING = 0b111
UT_MAP_TAB_KEY = "UT_MAP"

def main(args):
    import atexit
    confirmation = atexit.register(input, "Press enter to close.")
    erargs, seed = Generate.main()
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
    main(args)

if __name__ == "__main__":
    launch(*sys.argv[1:])
