import logging
import sys
import os
import argparse
from Generate import main as Gmain
from BaseClasses import PlandoOptions

from . import HijackGenerator
from CommonClient import get_base_parser, handle_url_arg

logger = logging.getLogger()

def Hijacking_argparse(argv: list[str] | None = None) -> argparse.Namespace:
    from settings import get_settings
    settings = get_settings()
    defaults = settings.generator

    parser = argparse.ArgumentParser(description="CMD Generation Interface, defaults come from host.yaml.")
    parser.add_argument('--weights_file_path', default=defaults.weights_file_path,
                        help='Path to the weights file to use for rolling game options, urls are also valid')
    parser.add_argument('--sameoptions', help='Rolls options per weights file rather than per player',
                        action='store_true')
    parser.add_argument('--player_files_path', default=defaults.player_files_path,
                        help="Input directory for player files.")
    parser.add_argument('--seed', help='Define seed number to generate.', type=int)
    parser.add_argument('--multi', default=defaults.players, type=lambda value: max(int(value), 1))
    parser.add_argument('--spoiler', type=int, default=defaults.spoiler)
    parser.add_argument('--outputpath', default=settings.general_options.output_path,
                        help="Path to output folder. Absolute or relative to cwd.")  # absolute or relative to cwd
    parser.add_argument('--allow_quantity', action="store_true", default=defaults.allow_quantity,
                        help='Allows the use of the quantity option in yamls. Default is the set value in the host.yaml.')
    parser.add_argument('--race', action='store_true', default=defaults.race)
    parser.add_argument('--meta_file_path', default=defaults.meta_file_path)
    parser.add_argument('--log_level', default=defaults.loglevel, help='Sets log level')
    parser.add_argument('--log_time', help="Add timestamps to STDOUT",
                        default=defaults.logtime, action='store_true')
    parser.add_argument("--csv_output", action="store_true",
                        help="Output rolled player options to csv (made for async multiworld).")
    parser.add_argument("--plando", default=defaults.plando_options,
                        help="List of options that can be set manually. Can be combined, for example \"bosses, items\"")
    parser.add_argument("--skip_prog_balancing", action="store_true",
                        help="Skip progression balancing step during generation.")
    parser.add_argument("--skip_output", action="store_true",
                        help="Skips generation assertion and output stages and skips multidata and spoiler output. "
                             "Intended for debugging and testing purposes.")
    parser.add_argument("--spoiler_only", action="store_true",
                        help="Skips generation assertion and multidata, outputting only a spoiler log. "
                             "Intended for debugging and testing purposes.")
    args = parser.parse_args(argv)

    if args.skip_output and args.spoiler_only:
        parser.error("Cannot mix --skip_output and --spoiler_only")
    elif args.spoiler == 0 and args.spoiler_only:
        parser.error("Cannot use --spoiler_only when --spoiler=0. Use --skip_output or set --spoiler to a different value")

    if not os.path.isabs(args.weights_file_path):
        args.weights_file_path = os.path.join(args.player_files_path, args.weights_file_path)
    if not os.path.isabs(args.meta_file_path):
        args.meta_file_path = os.path.join(args.player_files_path, args.meta_file_path)
    args.plando = PlandoOptions.from_option_string(args.plando)

    return args

def main(args):
    import atexit
    confirmation = atexit.register(input, "Press enter to close.")
    if not args:
        args = Hijacking_argparse(args)
    erargs, seed = Gmain(args)
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
    pass


def launch(*args):
    main(args)

if __name__ == "__main__":
    launch(*sys.argv[1:])