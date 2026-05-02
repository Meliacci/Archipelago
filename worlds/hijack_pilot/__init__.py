from worlds.LauncherComponents import Component, components, Type, launch_subprocess, icon_paths
from worlds.AutoWorld import World

def launch_client(*args):
    from Utils import messagebox, version_tuple
    if version_tuple < (0, 6, 2):
        from CommonClient import gui_enabled
        if gui_enabled:
            messagebox("Failure", "Running incompatible version of AP; either downgrade Hijack or upgrade AP", True)
        else:
            print("Running incompatible version of AP; either downgrade Hijack or upgrade AP")
        return

    from worlds.LauncherComponents import launch
    from .HijackGui import launch as TCMain

    launch(TCMain, name="Hijack Generator", args=args)

class TrackerWorld(World):
    settings_key = "hijack_pilot"

    # to make auto world register happy so we can register our settings
    game = "Hijack - Pilot Generator"
    hidden = True
    item_name_to_id = {}
    location_name_to_id = {}

icon_paths["hijack_ico"] = f"ap:{__name__}/icon/icon.png"
components.append(
    Component(
        display_name="Hijack - Pilot Generator",
        cli=True,
        icon="hijack_ico",
        component_type=Type.MISC,
        func=launch_client,
        description="Generate a multiworld with the YAMLs in the players folder.",
        supports_uri=False,
        )
    )