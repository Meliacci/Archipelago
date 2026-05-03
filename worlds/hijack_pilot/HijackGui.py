import logging
import sys
from Generate import main as Gmain

from . import HijackGenerator

logger = logging.getLogger()

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
    main(args)

if __name__ == "__main__":
    launch(*sys.argv[1:])