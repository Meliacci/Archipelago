# Static Modes

DisableDebugModes
    Originally: 
0x08:00:0fe4
    Originally:If(key_hit(KEY_START)); b8 d5: bpl LAB_08000f58
    if(false){}:    b8 e7: b LAB_08000f58

# Set Initial Data

First We deal with The stuff that can later change at Runtime

We have the Ram Addresses for it, they Should not change but W/E, we have them
```
    '__data_start__':0x03002910,
    'Inventory':0x03002934,
    'InitializersLen':0x0300294c,
    'HardMode':0x0300294e,
    'ExtraChest':0x0300294f,
    'HammerMode':0x03002950,
```

It should be noted that Some of these get initialized with 
```
    # Section, AddressStart, Length, LoadAtMemoryROM
    ('.data',0x03002910,0x6b8,0x0803e8ac)
```

Meaning we calculate the difference to the base addres and Apply the Values at ROM 0x0803e8ac
```
    ('__data_start__',0x03002910,0x0,0x0803E8AC)
    ('Inventory',0x03002934,0x18,0x0803E8D0)
    ('InitializersLen',0x0300294c,0x02,0x0803E8E8)
    ('HardMode',0x0300294e,0x01,0x0803E8EA)
    ('ExtraChest',0x0300294f,0x01,0x0803E8EB)
    ('HammerMode',0x03002950,0x01,0x0803E8EC)
```

Now the Static Data at ROM

```
    ('Initializers',0x0803d28c,0xf0) # A single Initializer is 0x0f and has the Struct EInteractType, Better to build Programmatically
    ('humanTiles',0x08005224,0x200) # Eventually i wanna change this
    ('humanPal',0x08005424,0x10) # And if i do i would have to update this as well
```

## Should no longer be reachable but JUST in case you CAN Disable the Modes to the correct Ones
At address 0x08:00:0f30
On Reset:
    Originally: HammerMode=HammerMode^1; 53 40: eor r3, r2 (Where previously mov r2, #0x1)
    HammerMode=1;    01 23: mov r3, #0x01
    HammerMode=0;    00 23: mov r3, #0x01


At address 0x08:00:1026

On Reset:
    Originally: *PTRToHardmodeRam = *PTRToHardmodeRam ^ 1; 53 40: eor r3, r2 (Where previously mov r2, #0x1)
    *PTRToHardmodeRam=1;    01 23: mov r3, #0x01
    *PTRToHardmodeRam=0;    00 23: mov r3, #0x01

At address 0x08:00:0ff4

On Reset:
    Originally: *PTRTO_EXTRACHEST = *PTRTO_EXTRACHEST ^ 1; 53 40: eor r3, r2 (Where previously mov r2, #0x1)
    *PTRTO_EXTRACHEST=1;    01 23: mov r3, #0x01
    *PTRTO_EXTRACHEST=0;    00 23: mov r3, #0x01
<!-- 
# enum EInteractType   type;		//!< Interaction Type
# 	u8	        		 x, y;		//!< Position in Meta Tiles
# 	u16			        state;		//!< Initial tile
#     u16                target;
#     /*
#     * Pointer to Meta Tile Mappings (where Given index tile*4+[0-3] returns the S-tile to be used at each of the 4 Tiles that make up a Meta Tile)
#     */
# 	const u16            *MetaTiles;		//!< Tile Reference
#    u32 SCR_ENTRY *dst; //!< Screen Entry
###### For the u16 state
#     /*
#     * Target Behaviour Dependent on interaction Type:
#     * EIT_NONE
#     * 
#     * Does nothing when Interacted with
#     * 
#     * EIT_CHEST
#     * 
#     * Places Target Index from ItemMetaTiles into Coords
#     * 
#     * EIT_BUTTON
#     * 
#     * Used by Exactly 1 Tile, If Interacts,Deletes Wall at Target Coord Where 0xFF00 is X and 0x00FF is y
#     * 
#     * EIT_ENEMY
#     * 
#     * Health indicated by State
#     * Once Health Reaches 0, Replace with Target Item at Coords
#     * 
#     * EIT_BOSS
#     * 
#     * This Needs a Bit more Work. He will never have an item himself.
#     * Target indicates True Health, while State Gives out the Initial tiles for the Interactable 
#     * 
#     * EIT_WALL
#     * 
#     * State is interactable Wall Type (Breakable)
#     * Checks that Player has Target Item in Inventory
#     * If player has, Delete Wall at Coord
#     *  
#     * EIT_ITEM
#     * 
#     * Deletes tile Entry and Places Target item in Player Inventory
#     * 
#     */ -->
