import pkgutil
from typing import TYPE_CHECKING, Iterable, List, Optional, Collection
import hashlib
import Utils
import os
import settings
import logging

if TYPE_CHECKING:
    from . import GBAPQuestWorld

from worlds.Files import APProcedurePatch, APTokenMixin, APTokenTypes, APPatchExtension

from .options import HardMode, Hammer, ExtraStartingChest

GBAPQUEST_HASH="31343ab6a58782ed7b0107f43cd46b10"

class GBAPQuestSettings(settings.Group):
    """ Settings for the launcher """

    class RomFile(settings.UserFilePath):
        """File name of the GBAPQuest rom"""

        copy_to = "GBAPQuest.gba"
        description = "GBAPQuest ROM File"
        md5s = ["31343ab6a58782ed7b0107f43cd46b10", "c5721784e2ad386238540b38e225a45c", "616a101030cab5a993518d9fe34dcc4d"] # May need to remove this, idk

    rom_file: RomFile = RomFile(RomFile.copy_to)
    rom_start: bool = True

class GBAPQUESTProcedurePatch(APProcedurePatch, APTokenMixin):
    hash = GBAPQUEST_HASH
    patch_file_ending = ".apgbpq"
    result_file_ending = ".gba"
    game = "GBAPquest"

    procedure = [
        ("apply_tokens", ["token_data.bin"]), # this... SHOULD work?
    ]

    @classmethod
    def get_source_data(cls) -> bytes:
        with open(settings.get_settings().gbapquest_options.rom_file, "rb") as infile:
            base_rom_bytes = bytes(infile.read())
        return base_rom_bytes

ItemNameToInventoryIndex={ # this is Different to the ID fo the true world
    "Confetti Cannon": 0,
    "Hammer": 1,
    "Key": 2,
    "Shield": 3,
    "Sword": 4,
    "Health Upgrade": 5,
}
#define ITEM_ARCHIPELAGO 0x01
#define ITEM_CONFETTI 0x02
#define ITEM_HAMMER 0x03
#define ITEM_KEY 0x04
#define ITEM_SHIELD 0x05
#define ITEM_SWORD 0x06
#define ITEM_HEALTH 0x0107
ItemNameToGBAItemIDBytes={ # this is Different to the ID fo the true world
    "Confetti Cannon": [0x02, 0x00],
    "Hammer": [0x03, 0x00],
    "Key": [0x04, 0x00],
    "Shield": [0x05, 0x00],
    "Sword": [0x06, 0x00],
    "Health Upgrade": [0x07, 0x01],
    "APitem": [0x01, 0x00]
}

# ('Initializers',0x0803d28c,0xf0) # A single Initializer is 0x0f and has the Struct EInteractType, Better to build Programmatically

    # Chest 1-6
    # {EIT_CHEST, 3,5, 0x05, ITEM_HEALTH, inanimatesMetaTiles}, "Top Left Room Chest"
	# {EIT_CHEST, 3,9, 0x05, ITEM_CONFETTI, inanimatesMetaTiles},"Bottom Left Extra Chest"//0x02 Confetti Extra Chest
	# {EIT_CHEST, 3,11, 0x05, ITEM_SWORD, inanimatesMetaTiles}, "Bottom Left Chest"
	# {EIT_CHEST, 7,3, 0x05, ITEM_HEALTH, inanimatesMetaTiles}, "Top Middle Chest"
	# {EIT_CHEST, 10,11, 0x05, ITEM_SHIELD, inanimatesMetaTiles}, "Bottom Right Room Left Chest"
	# {EIT_CHEST, 11,11, 0x05, ITEM_HAMMER, inanimatesMetaTiles}, "Bottom Right Room Right Chest"://0x06, Hammer Turns into Confetti when not in hammer mode
    # Enemies 7-8
    # {EIT_BOSS, 11,3, 0x08, 2, bossMetaTiles},//Let's start this one at EasyMode
	# {EIT_ENEMY, 11,7, 0x01, ITEM_KEY, normal_enemyMetaTiles},//this one is also Easy mode, Hardmode Starts at 2
LocationNameToInitializerIndex = {
    "Top Left Room Chest": 1,
    "Bottom Left Extra Chest": 2,
    "Bottom Left Chest": 3,
    "Top Middle Chest": 4,
    "Bottom Right Room Left Chest": 5,
    "Bottom Right Room Right Chest": 6,
    "Right Room Enemy Drop": 8,
}

def write_tokens(world: "GBAPQuestWorld", patch: GBAPQUESTProcedurePatch) -> None:
    options = world.options

    MainFunctionBaseAddres=0x0cdc
    # Disable Mode Switching
    patch.write_token(APTokenTypes.WRITE, MainFunctionBaseAddres+0x0321, bytes([0xe7]))
    WalltMetaInitBaseAddress=0x075c
    # Disable HammerOverride from Initializer to Interactive Initializers (Make Bottom Left Right chest NOT always HammerOrConfetti)
    patch.write_token(APTokenTypes.WRITE, WalltMetaInitBaseAddress+0x6E, bytes([0x1b,0x00]))
    # Static Mode Toggles
    dataSectionBaseAddress=0x03e8c4
    if options.hard_mode.value:
        patch.write_token(APTokenTypes.WRITE, dataSectionBaseAddress+62, bytes([0x01]))
    else:
        patch.write_token(APTokenTypes.WRITE, dataSectionBaseAddress+62, bytes([0x00]))

    if options.extra_starting_chest.value:
        patch.write_token(APTokenTypes.WRITE, dataSectionBaseAddress+63, bytes([0x01]))
    else:
        patch.write_token(APTokenTypes.WRITE, dataSectionBaseAddress+63, bytes([0x00]))

    if options.hammer.value:
        patch.write_token(APTokenTypes.WRITE, dataSectionBaseAddress+64, bytes([0x01]))
    else:
        patch.write_token(APTokenTypes.WRITE, dataSectionBaseAddress+64, bytes([0x00]))
    
    StartInventoryItemList = world.multiworld.precollected_items[world.player]

    if StartInventoryItemList:
        # Modify the Starting Inventory on 0x03E8D0 for 0x18 bytes, where every item is 0x04 bytes meaning there are 6 Inventory Items Slots
        # typedef struct TItem
        # {
        #     /*
        #     * in the Form 0x00AA
        #     * If Health; 
        #     * 0x0107
        #     * 
        #     * Else;
        #     * 
        #     * 0x00 nothing (should remain unused)
        #     * 0x01 Archipelago Item
        #     * 0x02 Confetti Cannon
        #     * 0x03 Hammer
        #     * 0x04 Key
        #     * 0x05 Shield
        #     * 0x06 Sword
        #     *
        #     * */
        # 	u16			state;		
        # 	u8			count;		//!< Inventory Count of item (Confetti and Health Upgrades)
        # 	u8			used;		//!< Inventory Count of How many times it has been used (Confetti and Damage Receive)
        # }ALIGN(4) TItem;
        # TItem Inventory[]={//Does not care about AP items and Nothings, Initial State starts at 0x03E8D0
        #     {ITEM_CONFETTI,0x00,0},
        #     {ITEM_HAMMER,0x00,0},
        #     {ITEM_KEY,0,0},
        #     {ITEM_SHIELD,0,0},
        #     {ITEM_SWORD,0,0},
        #     {ITEM_HEALTH,1,0},
        # };
        DictionaryCountPerAPItem:dict[str,int] = dict()
        for APItem in StartInventoryItemList:
            if APItem.player == world.player: #for whatever case it does not Belong to this player, which would be weird
                DictionaryCountPerAPItem[APItem.name]=DictionaryCountPerAPItem.get(APItem.name,0)+1
        DictionaryCountPerAPItem["Health Upgrade"]=DictionaryCountPerAPItem.get("Health Upgrade",0)+1 # By default you start with one Health, and if we don't set it here as +1 you would start with one less health
        # Does not Need to be set if we leave it as Default anyways
        for key in DictionaryCountPerAPItem:
            if ItemNameToInventoryIndex.get(key,-1) != -1:# Negative index is invalid, 0 index is valid
                # We Add 2 Bytes since the first 2 Bytes are for the Item ID, Then Count, then How many have been used 
                patch.write_token(APTokenTypes.WRITE,dataSectionBaseAddress+36+ItemNameToInventoryIndex[key]*0x04+2,bytes([DictionaryCountPerAPItem.get(key,0)]))

    InitializersBaseAddress=0x03d2a4
    # We exit the inner `If Start Inventory` and  go to deal with the Local Items on the locations
    active_locations = world.multiworld.get_locations(world.player)
    for LocationInfo in active_locations:
        if LocationNameToInitializerIndex.get(LocationInfo.name,-1) != -1:# Negative index is invalid, 0 index is valid
            if LocationInfo.item and LocationInfo.item.player == world.player:# They belong to the Own game letting you see Items as what they are. Only works for Local items
                patch.write_token(APTokenTypes.WRITE,InitializersBaseAddress+LocationNameToInitializerIndex[LocationInfo.name]*0x10+0x06,bytes(ItemNameToGBAItemIDBytes.get(LocationInfo.item.name, [0x01,0x00])))
            else:
                # Every other Game's Items is a simple AP item Sprite, so we don't compare their Name with anything
                # We could in theory parse the Name for a similar Sprite, but i don't feel like it :p, maybe something to do later
                patch.write_token(APTokenTypes.WRITE,InitializersBaseAddress+LocationNameToInitializerIndex[LocationInfo.name]*0x10+0x06,bytes([0x01,0x00]))
        else:
            pass
    patch.write_file("token_data.bin", patch.get_token_binary())
