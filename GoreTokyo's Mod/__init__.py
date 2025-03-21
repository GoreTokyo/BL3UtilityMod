"""
Author: GoreTokyo
version: 1.0.2
Description:
This mod enhances the gameplay experience in Borderlands 3 with various features 
such as God Mode, Infinite Ammo, Noclip, and more. It provides additional 
customization options to optimize player experience.
"""

if True:
    assert __import__("mods_base").__version_info__ >= (1, 0), "Please update the SDK"

import unrealsdk
from typing import Any
from mods_base import build_mod, get_pc, keybind, hook, ENGINE, SliderOption, SpinnerOption, BoolOption, DropdownOption, Game, NestedOption
from ui_utils import show_hud_message
from unrealsdk.hooks import Type, add_hook, Block, remove_hook, inject_next_call
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct
from .commands import *

# Options
AutoSkipDialog = BoolOption("Auto Skip Dialog", False, description="Automatically skip all dialog.")
BlockQTD = BoolOption("Disable Quit to Desktop Button", True, "Yes", "No")
DeleteCorpses = BoolOption("Override Corpse Removal Time", True, "Yes", "No")
CorpseDespawnTime = SliderOption("Corpse Despawn Time in Seconds", 5.0, 0.1, 30.0, 0.1, False)
FlySpeedSlider = SliderOption("Noclip Speed", 600, 600, 25000, 100, True)
OneShotOnePercent = BoolOption("One Shot to 1% HP", False, description="Limit One Shot Mode to setting enemies' health to 1%.")

# State variables
god_mode = infinite_ammo = noclip = no_target = one_shot_mode = False

# Helper functions
def log_status(name: str, status: bool) -> None:
    log_message(f"{name}: {str(status)}")

def toggle_feature(feature: str, current_state: bool) -> bool:
    log_status(feature, not current_state)
    return not current_state

# Damage Hook for One Shot Mode
@hook("/Script/GbxGameSystemCore.DamageComponent:ReceiveAnyDamage", Type.PRE)
def receive_any_damage(obj: UObject, args: WrappedStruct, _3: Any, _4: BoundFunction) -> None:
    if one_shot_mode and args.InstigatedBy == get_pc() and get_pc().GetTeamComponent().IsHostile(obj.Outer):
        damage = obj.SetCurrentHealth if not OneShotOnePercent.value else lambda hp: obj.SetCurrentHealth(obj.GetMaxHealth() / 100)
        damage(0)

# Dialog Skip
@keybind("Skip Dialog", description="Skips the currently playing dialog.")
def skip_dialog() -> None:
    for dialog in unrealsdk.find_all("GbxDialogComponent", exact=False):
        if dialog.CurrentPerformance.DialogThreadID > 0:
            dialog.StopPerformance(dialog.CurrentPerformance.DialogThreadID, True)

@hook("/Script/GbxDialog.GbxDialogComponent:StartPerformance", Type.PRE)
def dialog_start_performance(*_: Any) -> None | type[Block]:
    return Block if AutoSkipDialog.value else None

# Drop Entire Inventory
@keybind("Drop Your Entire Inventory", description="Drops all items from the player's inventory.")
def drop_all_items() -> None:
    numofitems: int = len(get_pc().OakCharacter.GetInventoryComponent().InventoryList.Items)
    dropindex: int = 0
    while numofitems > 0:
        if get_pc().OakCharacter.GetInventoryComponent().InventoryList.Items[dropindex].PlayerDroppability > 0:
            dropindex +=1
        get_pc().OakCharacter.GetInventoryComponent().ServerDropItem(get_pc().OakCharacter.GetInventoryComponent().InventoryList.Items[dropindex].Handle, get_pc().Pawn.K2_GetActorLocation(), get_pc().K2_GetActorRotation())
        numofitems -= 1
    return None

# Corpse Despawn Time
@hook("/Script/GbxGameSystemCore.DamageComponent:ReceiveHealthDepleted", Type.PRE)
def set_corpse_despawn_time(obj: UObject, args: WrappedStruct, _3: Any, _4: BoundFunction) -> None:
    try:
        if DeleteCorpses.value == True:
            obj.GetOwner().CorpseState.bOverrideVisibleCorpseRemovalTime = True
            obj.GetOwner().CorpseState.OverrideVisibleCorpseRemovalTime = CorpseDespawnTime.value
    except:
        pass
    return None

# Invulnerable
@keybind("Invulnerable", description="Toggle invulnerable for the player.")
def toggle_god_mode() -> None:
    global god_mode
    pc = get_pc()
    pc.OakCharacter.OakDamageComponent.bGodMode = toggle_feature("God Mode", god_mode)
    god_mode = not god_mode

# Infinite Ammo
@keybind("Infinite Ammo", description="Toggle infinite ammo for the player.")
def toggle_infinite_ammo() -> None:
    global infinite_ammo
    pc = get_pc()
    pc.bInfiniteAmmo = toggle_feature("Infinite Ammo", infinite_ammo)
    infinite_ammo = not infinite_ammo

# Noclip
@keybind("Noclip", description="Toggle noclip mode for the player.")
def toggle_noclip() -> None:
    global noclip
    pc = get_pc()
    pc.OakCharacter.bActorEnableCollision = not noclip
    pc.OakCharacter.OakCharacterMovement.MovementMode = 5 if noclip else 1
    pc.OakCharacter.OakCharacterMovement.MaxFlySpeed.Value = FlySpeedSlider.value
    noclip = toggle_feature("Noclip", noclip)

# No Target
@keybind("No Target", description="Make enemies ignore the player.")
def toggle_no_target() -> None:
    global no_target
    pc = get_pc()
    pc.TeamComponent.bIsTargetableByNonPlayers = not pc.TeamComponent.bIsTargetableByNonPlayers
    pc.TeamComponent.bIsTargetableByAIPlayers = not pc.TeamComponent.bIsTargetableByAIPlayers
    no_target = toggle_feature("No Target", no_target)

# One Shot Mode
@keybind("One Shot Mode", description="Enable one-shot mode to instantly kill enemies.")
def one_shot() -> None:
    global one_shot_mode
    one_shot_mode = toggle_feature("One Shot Mode", one_shot_mode)
    if one_shot_mode:
        add_hook("/Script/GbxGameSystemCore.DamageComponent:ReceiveAnyDamage", Type.PRE, "ReceiveAnyDamageHook", receive_any_damage)
    else:
        remove_hook("/Script/GbxGameSystemCore.DamageComponent:ReceiveAnyDamage", Type.PRE, "ReceiveAnyDamageHook")

# Corpse Despawn Time
@hook("/Script/GbxGameSystemCore.DamageComponent:ReceiveHealthDepleted", Type.PRE)
def set_corpse_despawn_time(obj: UObject, args: WrappedStruct, _3: Any, _4: BoundFunction) -> None:
    if DeleteCorpses.value:
        try:
            obj.GetOwner().CorpseState.bOverrideVisibleCorpseRemovalTime = True
            obj.GetOwner().CorpseState.OverrideVisibleCorpseRemovalTime = CorpseDespawnTime.value
        except Exception:
            pass

# Kill All Enemies
@keybind("Kill All", description="Kill all hostile enemies in the area.")
def kill_all() -> None:
    for pawn in unrealsdk.find_all("OakCharacter", exact=False):
        if get_pc().GetTeamComponent().IsHostile(pawn):
            pawn.DamageComponent.SetCurrentHealth(-1)
            pawn.DamageComponent.SetCurrentShield(-1)

# Quit to Desktop Block
@hook("/Script/OakGame.GFxPauseMenu:OnQuitChoiceMade", Type.PRE)
def check_sqd(obj: UObject, args: WrappedStruct, _3: Any, _4: BoundFunction) -> type[Block] | None:
    if BlockQTD.value and args.ChoiceNameId == "QuitToDesktop":
        return Block
    return None

# Save Quit functionality
def ServerUpdateLevelVisibility(obj: UObject, args: WrappedStruct, _3: Any, _4: BoundFunction) -> None:
    for item in unrealsdk.find_all("GbxGFxListCell"):
        if item and item.ListIndex != -1 and "OnPlayClicked" in str(item.OnClicked):
            item.OwningMovie.OnContinueClicked(item, unrealsdk.make_struct("GbxMenuInputEvent"))
    remove_hook("/Game/Maps/MenuMap/MenuMap_P.MenuMap_P_C:FadeDownBlackScreen__FinishedFunc", Type.POST, "ServerUpdateLevelVisibility")

# Quick Save/Reload
@keybind("Quick Save/Reload", description="Quickly save and reload the game.")
def save_quit():
    if "MenuMap_P" not in str(ENGINE.GameViewport.World.CurrentLevel):
        unrealsdk.construct_object("GFxPauseMenu", get_pc()).OnQuitChoiceMade(None, "GbxMenu_Secondary1", unrealsdk.make_struct("GbxMenuInputEvent"))
        add_hook("/Game/Maps/MenuMap/MenuMap_P.MenuMap_P_C:FadeDownBlackScreen__FinishedFunc", Type.POST, "ServerUpdateLevelVisibility", ServerUpdateLevelVisibility)
    return

# Sell Looked at Item
@keybind("Sell Looked at Item", description="Sell the currently selected item on the ground.")
def sell_ground_item() -> None:
    selected_item = get_pc().UseComponent.CurrentlySelectedPickup
    if selected_item and selected_item.CachedInventoryBalanceComponent.MonetaryValue > 0 and "RarityData_00_Mission" not in str(selected_item.AssociatedInventoryRarityData):
        get_pc().ServerAddCurrency(selected_item.CachedInventoryBalanceComponent.MonetaryValue, unrealsdk.find_object("InventoryCategoryData", "/Game/Gear/_Shared/_Design/InventoryCategories/InventoryCategory_Money.InventoryCategory_Money"))
        unrealsdk.find_object("InventoryModuleSettings", "/Script/GbxInventory.Default__InventoryModuleSettings").PickupShrinkDuration = 0.25
        selected_item.SetLifeSpan(0.01)
        selected_item.OnRep_BumpAngularDir()
        selected_item.bIsActive = False
        log_message("Item sold.")
        print(f"Sold Item: {selected_item}")
    else:
        log_message("No valid item selected to sell.")

# Slow/Speed Up Time
@keybind("Slow Down Time", description="Slow down the game time.")
def slow_down_time() -> None:
    world_settings = ENGINE.GameViewport.World.PersistentLevel.WorldSettings
    world_settings.TimeDilation = 1 if world_settings.TimeDilation <= 0.125 else world_settings.TimeDilation / 2
    log_message(f"Game Speed: {world_settings.TimeDilation}")

@keybind("Speed Up Time", description="Speed up the game time.")
def speed_up_time() -> None:
    world_settings = ENGINE.GameViewport.World.PersistentLevel.WorldSettings
    world_settings.TimeDilation = 1 if world_settings.TimeDilation >= 32 else world_settings.TimeDilation * 2
    log_message(f"Game Speed: {world_settings.TimeDilation}")

# Self Revive
@keybind("Self Revive", description="Revive yourself when in Fight For Your Life state.")
def revive_self() -> None:
    pc = get_pc()
    if pc.OakCharacter.BPFightForYourLifeComponent.IsInDownState():
        pc.OakCharacter.BPFightForYourLifeComponent.ActivateSecondWind()
        log_message("Self Revived")
    else:
        log_message("You are not in down state.")

# Mod options
options = [
    FlySpeedSlider,
    BlockQTD,
    CorpseDespawnTime,
    DeleteCorpses,
    AutoSkipDialog,
    OneShotOnePercent,
]

build_mod(options=options)
