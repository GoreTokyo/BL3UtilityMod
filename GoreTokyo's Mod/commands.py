from argparse import Namespace
import unrealsdk
from mods_base import get_pc, Game, command
from ui_utils import show_hud_message

activePlayer: int = -1

hud_message_title = "GoreTokyo's Mod"

def log_message(message: str) -> None:
    """
    Displays a message on the HUD and prints it to the console.
    """
    show_hud_message(hud_message_title, message)
    print(f"[{hud_message_title}] {message}")

@command("help", description="Displays a list of available commands.")
def display_help(args: Namespace) -> None:
    log_message("Commands:\n[command] --help for more details on specific commands\ngive [itemserial]\nsend_mail [datatable] [rowname]\naddcurrency [currencytype] [amount]\nmaxlevel\nmaxsdus\nenablegr\nsetguardianrank [rank]\nsetguardiantokens [tokens]\ngiveskillpoints [points]\ntogglemayhem [value]\ngetmayhemseed\nsetmayhemseed [seed]")

@command("give", description="Adds an item to your inventory using a serial code from a save editor.")
def give_item(args: Namespace) -> None:
    pc = get_pc()
    serial_code = args.serial_code

    if "(" in serial_code and ")" in serial_code:
        start = serial_code.find("(") + 1
        end = serial_code.find(")")
        serial_code = serial_code[start:end]

    log_message(f'Adding serial code {serial_code} to inventory')

    if Game.get_current() is Game.BL3:
        pc.ServerAddGearToInventory(serial_code, 0)
    elif Game.get_current() is Game.WL:
        pc.ServerAddGearToInventory(serial_code, 0, 0)

    log_message("Successfully added to inventory")

give_item.add_argument("serial_code", help="Serial code from a save editor.")

@command("send_mail", description="Sends an item to your mailbox using a DataTable and row name.")
def send_mail_item(args: Namespace) -> None:
    table = args.datatable
    row = args.rowname
    get_pc().AddNPCMailItemFromTableRowHandle(unrealsdk.make_struct("DataTableRowHandle", DataTable=unrealsdk.find_object("DataTable", table), RowName=row))
    log_message("Item sent to your mailbox.")

send_mail_item.add_argument("datatable", help="Path and name of the DataTable containing the desired item.")
send_mail_item.add_argument("rowname", help="Row name in the DataTable corresponding to the item.")

@command("addcurrency", description="Adds currency to your account. Valid types: money, eridium, goldkey, diamondkey, vaultcard1key, vaultcard2key, vaultcard3key. Max value: 2147483647.")
def add_currency(args: Namespace) -> None:
    currency_map = {
        "money": "/Game/Gear/_Shared/_Design/InventoryCategories/InventoryCategory_Money.InventoryCategory_Money",
        "diamondkey": "/Game/Gear/_Shared/_Design/InventoryCategories/InventoryCategory_DiamondKey.InventoryCategory_DiamondKey",
        "eridium": "/Game/Gear/_Shared/_Design/InventoryCategories/InventoryCategory_Eridium.InventoryCategory_Eridium",
        "goldkey": "/Game/Gear/_Shared/_Design/InventoryCategories/InventoryCategory_GoldenKey.InventoryCategory_GoldenKey",
        "vaultcard1key": "/Game/Gear/_Shared/_Design/InventoryCategories/InventoryCategory_VaultCard1Key.InventoryCategory_VaultCard1Key",
        "vaultcard2key": "/Game/Gear/_Shared/_Design/InventoryCategories/InventoryCategory_VaultCard2Key.InventoryCategory_VaultCard2Key",
        "vaultcard3key": "/Game/Gear/_Shared/_Design/InventoryCategories/InventoryCategory_VaultCard3Key.InventoryCategory_VaultCard3Key",
    }

    currency_type = str(args.currency).lower()
    if currency_type in currency_map:
        category_data = unrealsdk.find_object("InventoryCategoryData", currency_map[currency_type])
        if currency_type in ["money", "eridium"]:
            get_pc().ServerAddCurrency(int(args.amount), category_data)
        else:
            get_pc().ServerUpdatePremiumCurrency(category_data, int(args.amount))

        log_message(f"Added {int(args.amount)} {currency_type}(s).")
    else:
        log_message(f"Invalid currency type: {currency_type}. Valid options are: {', '.join(currency_map.keys())}")

add_currency.add_argument("currency", help="Currency type to modify.")
add_currency.add_argument("amount", help="Amount to add.")

@command("maxlevel", description="Sets your character to level 72.")
def set_max_level(args: Namespace) -> None:
    get_pc().OakCharacter.PlayerBalanceComponent.AddExperience(9520932 - get_pc().OakCharacter.PlayerBalanceComponent.GetExperience(), 0, 0)
    log_message("You are now level 72.")

@command("maxsdus", description="Upgrades all SDUs to the maximum level.")
def max_sdu_upgrades(args: Namespace) -> None:
    for sdu in unrealsdk.find_all("OakSDUData")[1:]:
        get_pc().OakCharacter.AddSDU(sdu)
    log_message("All SDUs upgraded to the maximum level.")

@command("enablegr", description="Enables Guardian Rank before completing the story.")
def enable_guardian_rank(args: Namespace) -> None:
    get_pc().OakHUD.CachedExperienceBar.PlayerGuardianRank.ServerStartGuardianRankTracking()
    log_message("Guardian Rank enabled.")

@command("setguardianrank", description="Sets your Guardian Rank to a specified value.")
def set_guardian_rank(args: Namespace) -> None:
    get_pc().OakHUD.CachedExperienceBar.PlayerGuardianRank.SetGuardianRank(int(args.rank))
    log_message(f"Guardian Rank set to {args.rank}.")

set_guardian_rank.add_argument("rank", help="Guardian Rank value to set.")

@command("setguardiantokens", description="Sets your available Guardian Tokens.")
def set_guardian_tokens(args: Namespace) -> None:
    get_pc().OakHUD.CachedExperienceBar.PlayerGuardianRank.ServerSetAvailableTokens(int(args.tokens))
    log_message(f"{args.tokens} Guardian Tokens set.")

set_guardian_tokens.add_argument("tokens", help="Number of Guardian Tokens to set.")

@command("giveskillpoints", description="Grants a specified number of skill points.")
def give_skill_points(args: Namespace) -> None:
    get_pc().OakHUD.CachedExperienceBar.PlayerAbilityTree.GiveAbilityPoints(int(args.points))
    log_message(f"{args.points} skill points granted.")

give_skill_points.add_argument("points", help="Number of skill points to grant.")

@command("togglemayhem", description="Toggles Mayhem Mode on or off.")
def toggle_mayhem_mode(args: Namespace) -> None:
    get_pc().OakHud.GFxBossBar.OakGameState.MayhemModeState.bIsActive = bool(args.value)
    log_message("Mayhem Mode toggled.")

toggle_mayhem_mode.add_argument("value", help="True to enable, False to disable.")

@command("getmayhemseed", description="Displays the current Mayhem Mode modifier seed values.")
def get_mayhem_seed(args: Namespace) -> None:
    state = get_pc().OakHud.GFxBossBar.OakGameState.MayhemModeState
    log_message(f"Mayhem {state.MayhemLevel} Modifier Bits (ActiveSetsBits): {state.ReplicableSets.ActiveSetsBits} RandomSeed: {state.RandomSeed}")

@command("setmayhemseed", description="Changes the current Mayhem Mode modifier seed.")
def set_mayhem_seed(args: Namespace) -> None:
    state = get_pc().OakHud.GFxBossBar.OakGameState.MayhemModeState
    state.ReplicableSets.ActiveSetsBits = int(args.bits)
    state.RandomSeed = int(args.seed)
    log_message("Mayhem Modifiers set. Travel to a new map and return for changes to take effect.")

set_mayhem_seed.add_argument("bits", help="Value for active modifier bits.")
set_mayhem_seed.add_argument("seed", help="Value for random seed.")