import logging
from typing import TYPE_CHECKING

from sympy import false

from NetUtils import ClientStatus

from argparse import Namespace

import worlds._bizhawk as bizhawk
from worlds._bizhawk.client import BizHawkClient


if TYPE_CHECKING:
    from ..._bizhawk.context import BizHawkClientContext, BizHawkClientCommandProcessor
GBAPQ_logger = logging.getLogger('GBAPQ_BIZ')
AddressDictionary={
    'bossMetaTiles':0x08004e58,
    'humanTiles':0x0800523c,
    'humanPal':0x0800543c,
    'inanimatesMetaTiles':0x0800578c,
    'normal_enemyMetaTiles':0x08005bfc,
    'HardModeHealthToSprite':0x0803d28c,
    'Initializers':0x0803d2a4,
    '__bss_start__':0x03001504,
    'g_CoordChecked':0x03001524,
    'g_CoordLUT':0x03001624,
    'InteractiveInitializers':0x03001a24,
    'InteractiveInitializers':0x03001a24,
    'DiedThisFrame':0x03001b14,
    '__bss_end__':0x03002910,
    '__data_start__':0x03002910,
    'PRNG_Next':0x03002910,
    'Inventory':0x03002934,
    'InitializersLen':0x0300294c,
    'HardMode':0x0300294e,
    'ExtraChest':0x0300294f,
    'HammerMode':0x03002950,
    '__data_end__':0x03002fd0,
}

class GBAPquestClient(BizHawkClient):
    game = "GBAPQuest"
    system = "GBA"
    patch_suffix = ".apgbpq"

    async def validate_rom(self, ctx: "BizHawkClientContext") -> bool:
        try:
            # Check ROM name/patch version
            rom_name = ((await bizhawk.read(ctx.bizhawk_ctx, [(0x0A0, 9, "ROM")]))[0]).decode("ascii")
            if rom_name != "GBAPquest":
                return False  # Not a GBAPQUEST ROM
        except bizhawk.RequestFailedError:
            return False  # Not able to get a response, say no for now

        # This is a MYGAME ROM
        ctx.game = self.game
        ctx.items_handling = 0b001 # We Have already Dealt with Starting inventory and Local Items Via the Patch
        ctx.want_slot_data = False

        return True

    async def game_watcher(self, ctx: "BizHawkClientContext") -> None:
        from worlds._bizhawk import read, write
        # Ccontrol Safeguard
        if ctx.server is None:
            return
        
        if ctx.slot is None:
            return
        
        try:
            # Read save data
            location_data = await bizhawk.read(
                 ctx.bizhawk_ctx,
                 [(AddressDictionary.get('g_CoordChecked',0x03001524), 0x0100, "System Bus")]
             )
            # Check Game Goal (0xb3 is the Boss Location)
            if not ctx.finished_game and (location_data[0][0xB3]):
                await ctx.send_msgs([{
                    "cmd": "StatusUpdate",
                    "status": ClientStatus.CLIENT_GOAL
                }])
            new_checks = []
            for LocationInt in ctx.missing_locations:
                if (location_data[0][LocationInt]):
                    new_checks.append(LocationInt)

                      
            for new_check_id in new_checks:
                        ctx.locations_checked.add(new_check_id)
                        location = ctx.location_names.lookup_in_game(new_check_id)
                        GBAPQ_logger.info(
                            f'New Check: {location} ({len(ctx.locations_checked)}/'
                            f'{len(ctx.missing_locations) + len(ctx.checked_locations)})')
                        await ctx.send_msgs([{"cmd": 'LocationChecks', "locations": [new_check_id]}])
        except bizhawk.RequestFailedError:
            # The connector didn't respond. Exit handler and return to main loop to reconnect
            pass