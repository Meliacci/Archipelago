from typing import TYPE_CHECKING

from NetUtils import ClientStatus

from argparse import Namespace

import worlds._bizhawk as bizhawk
from worlds._bizhawk.client import BizHawkClient


if TYPE_CHECKING:
    from ..._bizhawk.context import BizHawkClientContext, BizHawkClientCommandProcessor

class GBAPquestClient(BizHawkClient):
    game = "GBAPquest"
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
        ctx.items_handling = 0b001
        ctx.want_slot_data = True

        return True

    async def game_watcher(self, ctx: "BizHawkClientContext") -> None:
        try:
            # Read save data
            # save_data = await bizhawk.read(
            #     ctx.bizhawk_ctx,
            #     [(0x3000100, 20, "System Bus")]
            # )[0]

            # # Check locations
            # if save_data[2] & 0x04:
            #     await ctx.send_msgs([{
            #         "cmd": "LocationChecks",
            #         "locations": [23]
            #     }])

            # # Send game clear
            # if not ctx.finished_game and (save_data[5] & 0x01):
            #     await ctx.send_msgs([{
            #         "cmd": "StatusUpdate",
            #         "status": ClientStatus.CLIENT_GOAL
            #     }])
            pass
        except bizhawk.RequestFailedError:
            # The connector didn't respond. Exit handler and return to main loop to reconnect
            pass