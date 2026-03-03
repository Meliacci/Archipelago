import copy
from random import choice
import string
import typing

from BaseClasses import CollectionState, Item, ItemClassification, MultiWorld, Tutorial
from settings import Group, Bool
from .Items import item_table, event_item_pairs, filler_items
from .Locations import location_table
from .Options import ReventureOptions
from .Regions import create_regions
from .Rules import set_rules
from worlds.AutoWorld import AutoLogicRegister, WebWorld, World
from .CustomRegions import ReventureGraph


class ReventureSettings(Group):
    class AllowExperimentalSetting(Bool):
        """Allows using the experimental region graph."""

    allow_experimental: typing.Union[AllowExperimentalSetting, bool] = False


class ReventureWeb(WebWorld):
    tutorials = [Tutorial(
        "Multiworld Setup Guide",
        "A guide to setting up Reventure for Archipelago. "
        "This guide covers single-player, multiworld, and related software.",
        "English",
        "reventure_en.md",
        "reventure/en",
        ["Droppel"]
    )]


class ReventureWorld(World):
    """
    An adventure game where you find creative ways to die (And sometimes win)
    """

    options_dataclass = ReventureOptions
    options: ReventureOptions
    game = "Reventure"
    topology_present = False
    data_version = 1
    web = ReventureWeb()
    required_client_version = (0, 4, 0)
    settings: typing.ClassVar[ReventureSettings]

    item_name_to_id = {name: data.code for name, data in item_table.items()}
    location_name_to_id = location_table

    region_graph: ReventureGraph

    def isExperimentalRegionGraph(self) -> bool:
        return self.options.experimentalRegionGraph and self.settings.allow_experimental

    def create_items(self):
        # Fill out our pool with our items from item_pool, assuming 1 item if not present in item_pool
        pool = []
        total_location_count = len(self.multiworld.get_unfilled_locations(self.player)) - len(event_item_pairs)
        for name, data in item_table.items():
            if data.event or data.special or data.filler: # Skip Events, Special items and Filler items
                continue
            item = ReventureItem(name, self.player)
            pool.append(item)

        # if self.isExperimentalRegionGraph():
        #     # Add Jump increase
        #     pool.append(self.create_item("Jump Increase"))
        #     pool.append(self.create_item("Jump Increase"))

        # Add Swords
        if self.isExperimentalRegionGraph(): # We disable this for the experimental region graph
            pool.append(self.create_item("Sword Pedestal"))
            pool.append(self.create_item("Sword Chest"))
        else:
            pool.append(self.create_item("Progressive Sword"))
            pool.append(self.create_item("Progressive Sword"))
            if self.options.treasureSword:
                pool.append(self.create_item("Progressive Sword"))
        
        # Handle Gems
        if self.options.randomizeGems:
            for _ in range(0, self.options.gemsInPool):
                pool.append(self.create_item("Gem"))

        # Handle Jump Increases
        total_jump_increases = self.options.logic.get("total_jump_increase", 0)
        total_jump_increases = int(total_jump_increases)
        for i in range(0, total_jump_increases):
            pool.append(self.create_item(f"Jump Increase"))

        # Fill pool with filler items
        for _ in range(0, total_location_count - len(pool)):
            pool.append(self.create_item(self.get_filler_item_name()))

        self.multiworld.itempool += pool

        # Place locked event items
        for event, item in event_item_pairs.items():
            event_item = ReventureItem(item, self.player)
            self.get_location(event).place_locked_item(event_item)

    def set_rules(self):
        set_rules(self.options, self.multiworld, self.player, self.isExperimentalRegionGraph())
        
        # from Utils import visualize_regions
        # state = self.multiworld.get_all_state(False)
        # # state.prog_items[self.player]["Volcano Geyser"] -= 1
        # state.update_reachable_regions(self.player)
        # visualize_regions(self.multiworld.get_region("Menu", self.player), "my_world.puml", show_entrance_names=True, regions_to_highlight=state.reachable_regions[self.player])

    def create_item(self, name: str) -> Item:
        return ReventureItem(name, self.player)

    def create_regions(self):
        self.region_graph = create_regions(self.options, self.multiworld, self.player, self.isExperimentalRegionGraph())

    def fill_slot_data(self) -> dict:
        slot_data = {}
        
        slot_data["endings"] = self.options.endings.value
        slot_data["randomizeGems"] = 1 if self.options.randomizeGems else 0
        slot_data["gemsInPool"] = self.options.gemsInPool.value
        slot_data["gemsRequired"] = self.options.gemsRequired.value
        slot_data["hardjumps"] = 1 if self.options.hardjumps else 0
        slot_data["hardcombat"] = 1 if self.options.hardcombat else 0
        slot_data["nonStopMode"] = self.options.nonStopMode.value
        slot_data["treasureSword"] = 1 if self.options.treasureSword else 0
        
        slot_data["experimentalRegionGraph"] = 1 if self.isExperimentalRegionGraph() else 0
        if self.isExperimentalRegionGraph():
            slot_data["spawn"] = self.options.logic.get("start_region", "LonksHouse")
            slot_data["itemlocations"] = self.options.logic.get("item_locations", "")
            slot_data["startingjumps"] = self.options.logic.get("starting_jumps", 3)
        return slot_data

    def get_filler_item_name(self) -> str:
        return choice(filler_items)


class ReventureItem(Item):
    game = "Reventure"

    def __init__(self, name, player: int = None):
        item_data = item_table[name]
        super(ReventureItem, self).__init__(
            name,
            ItemClassification.progression if item_data.progression else ItemClassification.filler,
            item_data.code, player
        )
