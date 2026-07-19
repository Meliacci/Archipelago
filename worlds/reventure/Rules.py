from BaseClasses import CollectionState, MultiWorld
from Options import PerGameCommonOptions
from .Options import ReventureOptions
from worlds.generic.Rules import set_rule, add_rule
import copy
import ast
from .Items import item_table

class ReventureTransformer(ast.NodeTransformer):
    def add_spaces(self, s):
        result = ""
        for char in s:
            if char.isupper() and result and result[-1] != " ":
                result += " "
            result += char
        return result

    def visit_Name(self, node):
        has_func = ast.Attribute(
            value=ast.Name(id="state", ctx=ast.Load()),
            attr="has",
            ctx=ast.Load()
        )

        if "JumpIncrease" in node.id:
            name, count = node.id.split("_")
            name = self.add_spaces(name)
            count = int(count)
            return ast.Call(
                func=has_func,
                args=[ast.Constant(name),
                      ast.Name(id="p", ctx=ast.Load()), 
                      ast.Constant(count)
                ],
                keywords=[]
            )
        return ast.Call(
            func=has_func,
            args=[ast.Constant(self.add_spaces(node.id)),
                  ast.Name(id="p", ctx=ast.Load()),
            ],
            keywords=[]
        )

    def visit_BinOp(self, node):
        # Convert `*` to `and`
        if isinstance(node.op, ast.Mult):
            return ast.BoolOp(
                op=ast.And(),
                values=[self.visit(node.left), self.visit(node.right)]
            )
        if isinstance(node.op, ast.Add):
            return ast.BoolOp(
                op=ast.Or(),
                values=[self.visit(node.left), self.visit(node.right)]
            )
        return self.generic_visit(node)

    def visit(self, node):
        # Only allow safe node types
        allowed = (
            ast.Expression,
            ast.BoolOp,
            ast.BinOp,
            ast.Name,
            ast.Load,
            ast.And,
            ast.Mult,
            ast.Constant,
            ast.Call,
            ast.Attribute,
        )
        if not isinstance(node, allowed):
            raise ValueError(f"Unsupported AST node: {type(node)}")
        return super().visit(node)

def compile_rule(rule_str: str, p: int):
    transformer = ReventureTransformer()
    asttree = ast.parse(rule_str, mode='eval')
    rule = transformer.visit(asttree)

    ast.fix_missing_locations(rule)
    lambda_func = ast.Expression(
        body=ast.Lambda(
            args=ast.arguments(
                posonlyargs=[],
                args=[ast.arg(arg='state')],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[]
            ),
            body=rule.body
        )
    )
    ast.fix_missing_locations(lambda_func)

    compiled = compile(lambda_func, filename="<ast>", mode="eval")
    return eval(compiled, {"p": p})

def set_rules(options: ReventureOptions, multiworld: MultiWorld, p: int, isExperimental: bool):
    if options.endings-1 >= 50:
        # Inverted because it's faster
        def has_endings(state: CollectionState, player: int, req: int) -> bool:
            count = 0
            locations = state.multiworld.get_locations(player)
            invreq = 100 - req
            for loc in locations:
                if loc.name == "100: The End":
                    continue
                count += not loc.can_reach(state)
                if count >= invreq:
                    return False
            return True
    else:
        def has_endings(state: CollectionState, player: int, req: int) -> bool:
            count = 0
            locations = state.multiworld.get_locations(player)
            for loc in locations:
                if loc.name == "100: The End":
                    continue
                count += loc.can_reach(state)
                if count >= req:
                    return True
            return False
    
    if isExperimental:
        for (loc_name, rule_str) in options.logic.items():
            if loc_name == "start_region" or loc_name == "item_locations" or loc_name == "starting_jumps" or loc_name == "total_jump_increase":
                continue
            loc_name = loc_name.replace("_", " ")
            location = multiworld.get_location(loc_name, p)
            if rule_str == "1":
                set_rule(location, lambda state: True)
            else:
                set_rule(location, compile_rule(rule_str, p))
        requiredAmount = (options.gemsInPool * options.gemsRequired) // 100
        set_rule(multiworld.get_location("100: The End", p), lambda state: has_endings(state, p, options.endings-1) and state.has("Gem", p, requiredAmount))
        multiworld.completion_condition[p] = lambda state: state.has("Victory", p)
        return
    
    def has_burger(state: CollectionState, p: int) -> bool:
        return state.has("Burger", p) and state.has("Dark Stone Lever Middle", p)
    
    def has_darkstone(state: CollectionState, p: int) -> bool:
        return state.has_all(["Dark Stone", "Dark Stone Lever Middle"], p)

    def has_chicken(state: CollectionState, p: int) -> bool:
        return state.has("Chicken", p)
    
    def has_nuke(state: CollectionState, player: int) -> bool:
        return state.has_all(["Nuke", "Hook"], player)
    
    if options.treasureSword:
        def has_sword(state: CollectionState, p):
            if state.has("Progressive Sword", p, 2):
                return True
            elif state.has("Progressive Sword", p, 1):
                return state.has("Shovel", p) and state.has_any(["Hook", "Waterfall Geyser"], p)
            else:
                return False
    else:
        def has_sword(state: CollectionState, p):
            return state.has("Progressive Sword", p)
    
    def has_weight(state: CollectionState, player: int, req: int) -> bool:
        weightedItems = 0
        if has_sword(state, player):
            weightedItems += 1
        if state.has("Shovel", player):
            weightedItems += 1
        if state.has("Shield", player):
            weightedItems += 1
        if state.has("Bombs", player):
            weightedItems += 1
        if state.has("Hook", player):
            weightedItems += 1
        if state.has("Lava Trinket", player):
            weightedItems += 1
        if state.has("Whistle", player):
            weightedItems += 1
        if state.has("Boomerang", player):
            weightedItems += 1
        if has_nuke(state, player):
            weightedItems += 1
        if has_darkstone(state, player):
            weightedItems += 1
        if has_chicken(state, player):
            weightedItems += 1
        return weightedItems >= req
    
    def has_items(state: CollectionState, player: int, req: int) -> bool:
        items = 0
        valid_items = ["Hook", "Bombs", "Shield", "Shovel",
                       "Lava Trinket", "Whistle", "Boomerang", "Mister Hugs", 
                       "Map", "Compass"]
        for item in valid_items:
            if state.has(item, player):
                items += 1
        if has_sword(state, player):
            items += 1
        if has_nuke(state, player):
            items += 1
        if has_darkstone(state, player):
            items += 1
        if has_chicken(state, player):
            items += 1
        if has_burger(state, player):
            items += 1
        return items >= req
    

    def can_reach_princessportal_with_item(state: CollectionState, player: int) -> bool:
        return state.has("Mirror Portal", player) and (state.has("Vine", player)
                or (has_chicken(state, player)
                and (has_sword(state, player) 
                or state.has_any(["Hook", "Waterfall Geyser"], player))))

    def can_pass_castle_with_item(state: CollectionState, p: int) -> bool:
        return has_sword(state, p) or (has_chicken(state, p) and state.has("Princess Statue", p)) or (
            state.has_any(["Hook", "Shovel", "Shop Cannon", "Volcano Geyser", "Open Castle Floor", "Fairy Portal"], p))

    def can_reach_princess_with_item(state: CollectionState, player: int) -> bool:
        return state.has("Princess", player) and (can_reach_princessportal_with_item(state, player)
                                                          or state.has_any(["Hook", "Elevator Button", "Call Elevator Buttons"], player))
        

    set_rule(multiworld.get_location("01: It\'s Dangerous to be Near Tim", p), lambda state: has_sword(state, p) and state.has("Elder", p))
    set_rule(multiworld.get_location("02: Shit Happens", p), lambda state: state.has("Faceplant Stone", p))
    set_rule(multiworld.get_location("03: Please Nerf This", p), lambda state: True)
    set_rule(multiworld.get_location("04: Public Enemy", p), lambda state: has_sword(state, p)),
    set_rule(multiworld.get_location("05: Kingslayer", p), lambda state: has_sword(state, p) and state.has("King", p))
    set_rule(multiworld.get_location("06: The Floor is Lava", p), lambda state: True)
    set_rule(multiworld.get_location("07: Go Swimming", p), lambda state: True)
    set_rule(multiworld.get_location("08: Roll & Rock", p), lambda state: True)
    set_rule(multiworld.get_location("09: Customer is Always Right", p), lambda state: has_sword(state, p) and state.has("Shopkeeper", p))
    set_rule(multiworld.get_location("10: Gold Rush", p), lambda state: state.has("Shovel", p))
    set_rule(multiworld.get_location("11: Feline Company", p), lambda state: state.has("Mister Hugs", p))
    set_rule(multiworld.get_location("12: Hobbies", p), lambda state: state.has("Fishing Rod", p))
    set_rule(multiworld.get_location("13: Allergic to Cuteness", p), lambda state: state.has("Mister Hugs", p))
    set_rule(multiworld.get_location("14: Dracar-ish", p), lambda state: state.has("Dragon", p))
    set_rule(multiworld.get_location("15: Family Gathering", p), lambda state: True)
    set_rule(multiworld.get_location("16: Monster Hunter", p), lambda state: has_sword(state, p) and state.has("Dragon", p))
    set_rule(multiworld.get_location("17: Public Transport Next Time", p), lambda state: 
             state.has_any(["Shop Cannon", "Castle To Shop Cannon", "Dark Fortress Cannon", "Castle To Dark Fortress Cannon"], p))
    set_rule(multiworld.get_location("18: King of Hearts", p), lambda state: state.has_all(["Mister Hugs", "King"], p))
    set_rule(multiworld.get_location("19: Broken Heart", p), lambda state: state.has("Mister Hugs", p))
    set_rule(multiworld.get_location("20: Day Off", p), lambda state: True)
    set_rule(multiworld.get_location("21: You Nailed It", p), lambda state: True)
    set_rule(multiworld.get_location("22: Paperweight", p), lambda state: state.has("Anvil", p))
    set_rule(multiworld.get_location("23: True Beauty is inside", p), lambda state: state.has("Mimic", p))
    set_rule(multiworld.get_location("24: Strawberry", p), lambda state: state.has("Strawberry", p))
    set_rule(multiworld.get_location("25: Bully", p), lambda state: has_sword(state, p))
    set_rule(multiworld.get_location("26: Greedy Bastard", p), lambda state: has_weight(state, p, 5) and state.has("Hook", p)) # Not fully exhaustive
    set_rule(multiworld.get_location("27: Airstrike", p), lambda state: has_nuke(state, p) and state.has("Shop Cannon", p))
    set_rule(multiworld.get_location("28: Don\'t Try This at Home", p), lambda state: state.has("Bombs", p))
    set_rule(multiworld.get_location("29: The Man in the Steel Mask", p), lambda state: state.has_all(["Dragon", "Shield"], p))
    set_rule(multiworld.get_location("30: Subliminal Message", p), lambda state: True)
    set_rule(multiworld.get_location("31: Collateral Damage", p), lambda state: has_sword(state, p))
    set_rule(multiworld.get_location("32: You Monster", p), lambda state: has_sword(state, p) and state.has("Boulder", p))
    set_rule(multiworld.get_location("33: Leap of Faith", p), lambda state: True)
    set_rule(multiworld.get_location("34: -1st Floor", p), lambda state: state.has_any(["Elevator Button", "Call Elevator Buttons", "Princess"], p))
    set_rule(multiworld.get_location("35: Wastewater", p), lambda state: state.has("Sewer Pipe", p))
    set_rule(multiworld.get_location("36: Fireproof", p), lambda state: state.has_all(["Dragon", "Lava Trinket"], p))
    set_rule(multiworld.get_location("37: Free Hugs", p), lambda state: state.has_all(["Shopkeeper", "Mister Hugs"], p))
    set_rule(multiworld.get_location("38: Oh Boy, I\'m so Hungry", p), lambda state: state.has("Dark Stone Lever Left", p))
    set_rule(multiworld.get_location("39: Everything is Terrible", p), lambda state: True)
    set_rule(multiworld.get_location("40: Sexy Beard", p), lambda state: state.has("Mister Hugs", p) and state.has("Elder", p))
    set_rule(multiworld.get_location("41: Post-Traumatic Stress Disorder", p), lambda state: state.has_all(["Dragon", "Lava Trinket", "Shield"], p))
    set_rule(multiworld.get_location("42: Sneaky Bastard", p), lambda state: state.has("Princess", p))
    set_rule(multiworld.get_location("43: Dinner for Two", p), lambda state: state.has_all(["Dragon", "Mister Hugs"], p))
    set_rule(multiworld.get_location("44: Bad Leverage", p), lambda state: state.has("Dark Stone Lever Right", p))
    set_rule(multiworld.get_location("45: Well Excuuuuse Me, Princess", p), lambda state: state.has("Princess", p))
    set_rule(multiworld.get_location("46: Extreme Sports", p), lambda state: True)
    set_rule(multiworld.get_location("47: Harakiri", p), lambda state: has_sword(state, p))
    if options.hardjumps:
        set_rule(multiworld.get_location("48: It\'s my First Day", p), lambda state: True)
    else:
        set_rule(multiworld.get_location("48: It\'s my First Day", p), lambda state: state.has("Hook", p)
             or (can_pass_castle_with_item(state, p) and has_chicken(state, p)))
    if options.hardcombat:
        set_rule(multiworld.get_location("49: Victory Royale", p), lambda state: has_sword(state, p))
    else:
        set_rule(multiworld.get_location("49: Victory Royale", p), lambda state: has_sword(state, p)
             and state.has("Shield", p))
    set_rule(multiworld.get_location("50: P0wned", p), lambda state: state.has("Princess", p))
    set_rule(multiworld.get_location("51: Politics", p), lambda state: state.has("Princess", p))
    set_rule(multiworld.get_location("52: I\'m Feeling Lucky", p), lambda state: state.has_all(["Princess", "Dark Fortress Cannon"], p))
    set_rule(multiworld.get_location("53: Videogames", p), lambda state: state.has("Princess", p))
    set_rule(multiworld.get_location("54: Paraphilia", p), lambda state: state.has("Mister Hugs", p) and state.has("Boulder", p))
    set_rule(multiworld.get_location("55: Escape Shortcut", p), lambda state: state.has("Princess", p))
    set_rule(multiworld.get_location("56: Refund Request", p), lambda state: has_nuke(state, p) and state.has("Castle To Shop Cannon", p)
             and can_pass_castle_with_item(state, p))
    set_rule(multiworld.get_location("57: Friendzoned", p), lambda state: state.has_all(["Mister Hugs", "Princess"], p))
    set_rule(multiworld.get_location("58: Dark Extreme Sports", p), lambda state: True)
    set_rule(multiworld.get_location("59: Away From Kingdom", p), lambda state: True)
    set_rule(multiworld.get_location("60: Viva La Resistance", p), lambda state: state.has("Bombs", p))
    if options.hardjumps:
        set_rule(multiworld.get_location("61: Syndicalism", p), lambda state: True)
    else:
        set_rule(multiworld.get_location("61: Syndicalism", p), lambda state: state.has("Hook", p)
             or (can_pass_castle_with_item(state, p) and has_chicken(state, p)))
    set_rule(multiworld.get_location("62: Jackpot", p), lambda state: state.has("Shovel", p) and (has_sword(state, p)
             or state.has_any(["Hook", "Waterfall Geyser"], p)))
    set_rule(multiworld.get_location("63: You Don\'t Mess With Chicken", p), lambda state: has_sword(state, p) and has_chicken(state, p))
    set_rule(multiworld.get_location("64: I Thought It Was A Mimic", p), lambda state: has_sword(state, p) and can_reach_princess_with_item(state, p))
    set_rule(multiworld.get_location("65: Overheal", p), lambda state: True)
    set_rule(multiworld.get_location("66: Finite War", p), lambda state: has_darkstone(state, p))
    set_rule(multiworld.get_location("67: Stay Determined", p), lambda state: True)
    if options.hardjumps:
        set_rule(multiworld.get_location("68: Otaku Fever", p), lambda state: True)
    else:
        set_rule(multiworld.get_location("68: Otaku Fever", p), lambda state: state.has("Princess", p))
    set_rule(multiworld.get_location("69: Quick and Dirty", p), lambda state: has_sword(state, p) and can_reach_princess_with_item(state, p))
    set_rule(multiworld.get_location("70: It\'s a Trap", p), lambda state: True)
    set_rule(multiworld.get_location("71: Sustainable Development", p), lambda state: has_items(state, p, 6) and (has_sword(state, p)
             or state.has_all(["Shovel", "Waterfall Geyser"], p) or (state.has("Bombs", p)
             and state.has_any(["Shop Cannon", "Volcano Geyser", "Open Castle Floor", "Fairy Portal"], p))))
    set_rule(multiworld.get_location("72: Ecologist", p), lambda state: state.has("Princess", p))
    set_rule(multiworld.get_location("73: Dark Love", p), lambda state: state.has_all(["Mister Hugs", "Princess"], p))
    if options.hardjumps or options.hardcombat:    
        set_rule(multiworld.get_location("74: Bittersweet Revenge", p), lambda state: has_sword(state, p)
             and state.has_all(["Shopkeeper", "Mimic", "Shop Cannon"], p)
             and state.has_any(["Call Elevator Buttons", "Elevator Button"], p))
    else:    
        set_rule(multiworld.get_location("74: Bittersweet Revenge", p), lambda state: has_sword(state, p)
             and state.has_all(["Shopkeeper", "Mimic", "Shop Cannon"], p)
             and state.has_any(["Call Elevator Buttons", "Elevator Button"], p)
             and state.has_any(["Bombs", "Shovel"], p))
    set_rule(multiworld.get_location("75: Please, Not Again", p), lambda state: state.has("Princess", p))
    set_rule(multiworld.get_location("76: A Waifu is You", p), lambda state: state.has("Princess", p))
    set_rule(multiworld.get_location("77: Battle Royale", p), lambda state: state.has("Vine", p) or (has_chicken(state, p) and (has_sword(state, p)
             or state.has("Hook", p) or (can_pass_castle_with_item(state, p) and state.has("Waterfall Geyser", p)))))
    set_rule(multiworld.get_location("78: Silver or Lead", p), lambda state: state.has("Princess", p))
    set_rule(multiworld.get_location("79: Good Ending", p), lambda state: has_chicken(state, p) and state.has("Mister Hugs", p))
    set_rule(multiworld.get_location("80: Chicken of Doom", p), lambda state: has_chicken(state, p) and can_pass_castle_with_item(state, p))
    set_rule(multiworld.get_location("81: Forever Together", p), lambda state: state.has("Princess", p))
    set_rule(multiworld.get_location("82: Perfect Crime", p), lambda state: state.has("Princess", p))
    set_rule(multiworld.get_location("83: We Have to Go Back", p), lambda state: state.has("Whistle", p))
    set_rule(multiworld.get_location("84: Not what you Expected", p), lambda state: has_nuke(state, p) and state.has("Dark Fortress Cannon", p) 
             and can_pass_castle_with_item(state, p))
    set_rule(multiworld.get_location("85: Hey, Listen", p), lambda state: has_sword(state, p) or state.has("Mister Hugs", p)
             or state.has("Boomerang", p))
    set_rule(multiworld.get_location("86: Full House", p), lambda state: has_sword(state, p) and state.has("Princess", p))
    set_rule(multiworld.get_location("87: Crunch Hell", p), lambda state: can_reach_princess_with_item(state, p)
             and ((has_sword(state, p) and (state.has("Hook", p) or (has_chicken(state, p) and state.has("Shovel", p)))) 
             or (state.has("Boomerang", p) and state.has_any(["Hook", "Shovel"], p))))
    set_rule(multiworld.get_location("88: Odyssey", p), lambda state: has_weight(state, p, 4) and state.has_all(["Hook", "Desert Geyser West"], p))
    if options.hardjumps:
        set_rule(multiworld.get_location("89: Intestinal Parasites", p), lambda state: state.has("Princess", p) or (state.has("Shovel", p)))
    else:
        set_rule(multiworld.get_location("89: Intestinal Parasites", p), lambda state: state.has("Princess", p) or (state.has_all(["Shovel", "Lava Trinket"], p)))
    set_rule(multiworld.get_location("90: Try Harder", p), lambda state: state.has("Shield", p) and can_reach_princess_with_item(state, p)
             and can_pass_castle_with_item(state, p))
    set_rule(multiworld.get_location("91: Jump Around", p), lambda state: has_weight(state, p, 4) and state.has("Hook", p))
    set_rule(multiworld.get_location("92: First Date", p), lambda state: state.has_all(["Princess", "Dragon"], p))
    set_rule(multiworld.get_location("93: Dark Delivery Boy", p), lambda state: has_darkstone(state, p) and state.has("Princess", p)
             and state.has_any(["Hook", "Elevator Button", "Call Elevator Buttons"], p))
    set_rule(multiworld.get_location("94: Influencers", p), lambda state: state.has("Princess", p))
    set_rule(multiworld.get_location("95: Hypothermia", p), lambda state: True)
    set_rule(multiworld.get_location("96: Pirates", p), lambda state: True)
    set_rule(multiworld.get_location("97: Swimming Into the Sunset", p), lambda state: True)
    set_rule(multiworld.get_location("98: Suspension Points", p), lambda state: has_burger(state, p) and state.has("Mimic", p)
             and (state.has_any(["Hook", "Elevator Button", "Call Elevator Buttons"], p) or state.has_all(["Vine", "Mirror Portal"], p)))
    set_rule(multiworld.get_location("99: Delivery Boy", p), lambda state: has_burger(state, p) and state.has("King", p))
    if options.randomizeGems: # Randomized Gems
        requiredAmount = (options.gemsInPool * options.gemsRequired) // 100
        set_rule(multiworld.get_location("100: The End", p), lambda state: has_endings(state, p, options.endings-1) and state.has("Gem", p, requiredAmount))
    else: #Vanilla Gems
        set_rule(multiworld.get_location("100: The End", p), lambda state: has_endings(state, p, options.endings-1) and state.has_all(["Shovel", "Hook"], p) and has_weight(state, p, 4))

    multiworld.completion_condition[p] = lambda state: state.has("Victory", p)

