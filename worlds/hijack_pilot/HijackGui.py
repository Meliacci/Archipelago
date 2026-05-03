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
