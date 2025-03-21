"""
Author: GoreTokyo
version: 1.0.1
Description:
This mod enhances the gameplay experience in Borderlands 3 with various features 
such as God Mode, Infinite Ammo, Noclip, and more. It provides additional 
customization options to optimize player experience.

Key Features:
- God Mode: Become invincible.
- Infinite Ammo: Never run out of ammunition.
- Noclip: Move freely through walls and objects.
- One-Shot Mode: Defeat enemies with a single hit.
- Dialog Skip: Automatically or manually skip in-game dialogs.
- Corpse Despawn Time: Adjust corpse removal timing.
- Quick Save/Reload: Instantly save and reload the game.
- Sell Looked-at Item: Instantly sell the selected ground item.
- Time Manipulation: Slow down or speed up game time.
- Self Revive: Revive yourself when in Fight For Your Life state.

This mod is designed to enhance player control and provide convenience.
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
AutoSkipDialog: BoolOption = BoolOption("Auto Skip Dialog", False, description="Automatically skip all dialog as soon as it is started, including idle dialog.")
BlockQTD: BoolOption = BoolOption("Disable Quit to Desktop Button", True, "Yes", "No")
DeleteCorpses: BoolOption = BoolOption("Override Corpse Removal Time", True, "Yes", "No")
CorpseDespawnTime: SliderOption = SliderOption("Corpse Despawn Time in Seconds", 5.0, 0.1, 30.0, 0.1, False)
FlySpeedSlider: SliderOption = SliderOption("Noclip Speed", 600, 600, 25000, 100, True)
OneShotOnePercent = BoolOption("One Shot to 1% HP", False, description="Limit One Shot Mode to setting enemies' health to 1%.")

# State variables
infinite_ammo: bool = False
noclip: bool = False
godmode: bool = False
one_shot_mode: bool = False

# Damage Hook for One Shot Mode
@hook("/Script/GbxGameSystemCore.DamageComponent:ReceiveAnyDamage", Type.PRE)
def receive_any_damage(obj: UObject, args: WrappedStruct, _3: Any, _4: BoundFunction) -> None:
    if not one_shot_mode:
        return
    pc = get_pc()
    if args.InstigatedBy != pc or not pc.GetTeamComponent().IsHostile(obj.Outer):
        return
    obj.SetCurrentShield(0)
    if OneShotOnePercent.value:
        one_percent = obj.GetMaxHealth() / 100
        obj.SetCurrentHealth(one_percent)
    else:
        obj.SetCurrentHealth(0)

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

# God Mode
@keybind("God Mode", description="Toggle invincibility for the player.")
def god_mode() -> None:
    pc = get_pc()
    pc.OakCharacter.OakDamageComponent.bGodMode = not pc.OakCharacter.OakDamageComponent.bGodMode
    log_message(f"God Mode: {str(pc.OakCharacter.OakDamageComponent.bGodMode)}")

# Infinite Ammo
@keybind("Infinite Ammo", description="Toggle infinite ammo for the player.")
def toggle_infinite_ammo() -> None:
    global infinite_ammo
    pc = get_pc()
    pc.bInfiniteAmmo = not pc.bInfiniteAmmo
    infinite_ammo = not infinite_ammo
    log_message(f"Infinite Ammo: {str(infinite_ammo)}")

# Kill All Enemies
@keybind("Kill All", description="Kill all hostile enemies in the area.")
def kill_all() -> None:
    is_hostile = get_pc().GetTeamComponent().IsHostile
    for pawn in unrealsdk.find_all("OakCharacter", exact=False):
        if not is_hostile(pawn):
            continue
        damage_comp = pawn.DamageComponent
        damage_comp.SetCurrentShield(-1)
        damage_comp.SetCurrentHealth(-1)

# Noclip Toggle
@keybind("Noclip", description="Toggle noclip mode for the player.")
def toggle_noclip() -> None:
    global noclip
    pc = get_pc()
    if noclip:
        pc.OakCharacter.bActorEnableCollision = True
        pc.OakCharacter.OakCharacterMovement.MovementMode = 1
        pc.OakCharacter.OakDamageComponent.MinimumDamageLaunchVelocity = 370
    else:
        pc.OakCharacter.OakCharacterMovement.MovementMode = 5
        pc.OakCharacter.bActorEnableCollision = False
        pc.OakCharacter.OakDamageComponent.MinimumDamageLaunchVelocity = 9999999999
    pc.OakCharacter.OakCharacterMovement.MaxFlySpeed.Value = FlySpeedSlider.value
    noclip = not noclip
    log_message(f"Noclip: {str(noclip)}")

@keybind("No Target", description="Make enemies ignore the player.")
def no_target() -> None:
     get_pc().TeamComponent.bIsTargetableByNonPlayers = not get_pc().TeamComponent.bIsTargetableByNonPlayers
     get_pc().TeamComponent.bIsTargetableByAIPlayers = not get_pc().TeamComponent.bIsTargetableByAIPlayers
     log_message(f"No Target: {str(not get_pc().TeamComponent.bIsTargetableByNonPlayers)}")

# One Shot Mode
@keybind("One Shot Mode", description="Enable one-shot mode to instantly kill enemies.")
def one_shot() -> None:
    global one_shot_mode
    one_shot_mode = not one_shot_mode
    log_message(f"One Shot Mode: {str(one_shot_mode)}")
    if one_shot_mode:
        add_hook("/Script/GbxGameSystemCore.DamageComponent:ReceiveAnyDamage", Type.PRE, "ReceiveAnyDamageHook", receive_any_damage)
    else:
        remove_hook("/Script/GbxGameSystemCore.DamageComponent:ReceiveAnyDamage", Type.PRE, "ReceiveAnyDamageHook")

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

# Slow Down Time
@keybind("Slow Down Time", description="Slow down the game time.")
def slow_down_time() -> None:
    world_settings = ENGINE.GameViewport.World.PersistentLevel.WorldSettings
    if world_settings.TimeDilation <= 0.125:
        world_settings.TimeDilation = 1
    else:
        world_settings.TimeDilation /= 2
    log_message(f"Game Speed: {str(world_settings.TimeDilation)}")

# Speed Up Time
@keybind("Speed Up Time", description="Speed up the game time.")
def speed_up_time() -> None:
    world_settings = ENGINE.GameViewport.World.PersistentLevel.WorldSettings
    if world_settings.TimeDilation >= 32:
        world_settings.TimeDilation = 1
    else:
        world_settings.TimeDilation *= 2
    log_message(f"Game Speed: {str(world_settings.TimeDilation)}")

# Self Revive
@keybind("Self Revive", description="Revive yourself when in Fight For Your Life state.")
def revive_self() -> None:
    pc = get_pc()
    if pc.OakCharacter.BPFightForYourLifeComponent.IsInDownState():
        pc.OakCharacter.BPFightForYourLifeComponent.ActivateSecondWind()
        log_message("Self Revived")
    else:
        log_message("You are not in down state.")

options = [
    FlySpeedSlider,
    BlockQTD,
    CorpseDespawnTime,
    DeleteCorpses,
    AutoSkipDialog,
    OneShotOnePercent,
]

build_mod(options=options)