from worlds.LauncherComponents import Component, components, Type, launch_subprocess, icon_paths
from settings import Group, Bool, UserFolderPath, _world_settings_name_cache
from typing import Any, ClassVar, NamedTuple, Callable,Optional
from worlds.AutoWorld import World
from BaseClasses import CollectionState,Entrance
from collections import Counter
from enum import Enum

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
    print("Launching Hijack Client")
    launch(TCMain, name="Hijack Generator", args=args)

HIJACK_VERSION = "v0.0.1"

class CurrentTrackerState(NamedTuple):
    all_items: Counter
    prog_items: Counter
    glitched_locations: list[str]
    events: list[str]
    event_locations: list[str]
    in_logic_locations: list[str]
    in_logic_regions: list[str]
    unconnected_entrances: list[Entrance]
    readable_locations: list[str]
    hinted_locations: list
    state: Optional[CollectionState]
    glitches_state: Optional[CollectionState]

    @staticmethod
    def init_empty_state() -> "CurrentTrackerState":
        return CurrentTrackerState(Counter(),Counter(),[],[],[],[],[],[],[],[],None,None)

class DeferredEntranceMode(Enum):
    """Determines how worlds should be allowed to use deferred entrances
    on: Force worlds to disconnect entrances
    default: Allow worlds to decide if entrances should be deferred
    off: Force worlds to connect all entrances
    """

    forced = "on"
    default = "default"
    disabled = "off"

class TrackerSettings(Group):
    class TrackerPlayersPath(UserFolderPath):
        """Players folder for UT look for YAMLs"""

    class RegionNameBool(Bool):
        """Show Region names in the UT tab"""

    class LocationNameBool(Bool):
        """Show Location names in the UT tab"""

    class HideExcluded(Bool):
        """Have the UT tab ignore excluded locations"""
    
    class UseSplitMapIcons(Bool):
        """Use split icons rather then mixed for the UT map tab"""
    
    class DisplayGlitchedLogic(Bool):
        """Enable showing Glitched/yellow logic in tracker tab"""
    
    class SettingDeferredEntranceMode(str):
        """Determines how worlds should be allowed to use deferred entrances
        on: Force worlds to disconnect entrances
        default: Allow worlds to decide if entrances should be deferred
        off: Force worlds to connect all entrances
        """

    class SaveEnteredCommands(Bool):
        """Enable saving which locations you've ignored and which items you've manually collected using the commands.
        These will be saved per seed and slot.
        """

    player_files_path: TrackerPlayersPath = TrackerPlayersPath("Players")
    include_region_name: RegionNameBool | bool = False
    include_location_name: LocationNameBool | bool = True
    hide_excluded_locations: HideExcluded | bool = False
    use_split_map_icons: UseSplitMapIcons | bool = True
    enforce_deferred_entrances: SettingDeferredEntranceMode | str = "default"
    display_glitched_logic: DisplayGlitchedLogic | bool = True
    save_entered_commands: SaveEnteredCommands | bool = True


class TrackerWorld(World):
    settings: ClassVar[TrackerSettings]
    settings_key = "hijack_pilot"

    # to make auto world register happy so we can register our settings
    game = "Hijack - Pilot Generator"
    hidden = True
    item_name_to_id = {}
    location_name_to_id = {}

icon_paths["hijack_ico"] = f"ap:{__name__}/icon/icon.png"
components.append(
    Component(
        "Hijack - Pilot Generator",
        None,
        cli=True,
        func=launch_client,
        description="Generate a multiworld with the YAMLs in the players folder.",
        component_type=Type.MISC,
        icon="hijack_ico")
    )
