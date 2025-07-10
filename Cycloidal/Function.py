"""This file acts as the main module for this script."""

import traceback
import adsk.core
import adsk.fusion
# import adsk.cam

from . import Gen 

import os
from .. import fusionAddInUtils as futil
from .. import config

# Initialize the global variables for the Application and UserInterface objects.
app = adsk.core.Application.get()
ui  = app.userInterface

#globals
CMD_NAME = os.path.basename(os.path.dirname(__file__))
CMD_ID = f'{config.ADDIN_NAME}_{CMD_NAME}_v2'
CMD_Description = "Cycloidal Gear Generator"
IS_PROMOTED = False

WORKSPACE_ID = config.design_workspace
TAB_ID = config.tools_tab_id
TAB_NAME = config.my_tab_name

PANEL_ID = config.my_panel_id
PANEL_NAME = config.my_panel_name
PANEL_AFTER = config.my_panel_after

ICON_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources')

design = app.activeProduct
userParams = design.userParameters

local_handlers = []

def start():
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)
    
    #to create
    futil.add_handler(cmd_def.commandCreated, command_created) 
    
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    
    toolbar_tab = workspace.toolbarTabs.itemById(TAB_ID)
    if toolbar_tab is None:
        toolbar_tab = workspace.toolbarTabs.add(TAB_ID, TAB_NAME)
        
    panel = toolbar_tab.toolbarPanels.itemById(PANEL_ID)
    if panel is None:
        panel = toolbar_tab.toolbarPanels.add(PANEL_ID, PANEL_NAME, PANEL_AFTER, False)
        
    # Create the command control, i.e. a button in the UI.
    control = panel.controls.addCommand(cmd_def)

    # Now you can set various options on the control such as promoting it to always be shown.
    control.isPromoted = IS_PROMOTED

def stop():
    
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    toolbar_tab = workspace.toolbarTabs.itemById(TAB_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)
    
    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()

    # Delete the panel if it is empty
    if panel.controls.count == 0:
        panel.deleteMe()

    # Delete the tab if it is empty
    if toolbar_tab.toolbarPanels.count == 0:
        toolbar_tab.deleteMe()

def command_created(args: adsk.core.CommandCreatedEventArgs):
    futil.log(f'{CMD_NAME} Command Created Event')
    
     # Connect to the events that are needed by this command.
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)

    inputs = args.command.commandInputs
    initial_value_dist = adsk.core.ValueInput.createByString('0.0 cm')
    
    inputs.addValueInput('rotor_radius_input', 'Rotor Radius', 'mm', adsk.core.ValueInput.createByReal(10.0))
    inputs.addValueInput('eccentricity_input', 'Eccentricity', 'mm', adsk.core.ValueInput.createByReal(0.75))
    inputs.addValueInput('roller_radius_input', 'Roller Radius', 'mm', adsk.core.ValueInput.createByReal(1.5))
    inputs.addValueInput('center_hole_radius_input', 'Center Hole Radius', 'mm', adsk.core.ValueInput.createByReal(0.0))
    inputs.addIntegerSpinnerCommandInput('points_per_tooth_input', 'Points per Tooth', 1, 20, 1, 6)
    inputs.addIntegerSpinnerCommandInput('gear_ratio_input', 'Gear Ratio', 1, 200, 1, 10)
    
    
def command_execute(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Execute Event')
    inputs = args.command.commandInputs


    gear_ratio = inputs.itemById("gear_ratio_input").value
    R = inputs.itemById("rotor_radius_input").value   
    E = inputs.itemById("eccentricity_input").value   
    Rr = inputs.itemById("roller_radius_input").value 
    center_hole_radius = inputs.itemById("center_hole_radius_input").value  
    points_per_tooth = inputs.itemById("points_per_tooth_input").value

    Gen.generate_cyloid(R, E, Rr, gear_ratio, center_hole_radius, points_per_tooth)

    # not really needed
    log_command_inputs(inputs)

    
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    inputs = args.input.parentCommand.commandInputs
    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}')
    
def command_destroy(args: adsk.core.CommandEventArgs):
    global local_handlers
    local_handlers = []
    futil.log(f'{CMD_NAME} Command Destroy Event')

def log_command_inputs(inputs):
    seperator = '\n***************************\n'
    futil.log(seperator)
    futil.log('Summary of Command Inputs')
    futil.log(seperator)

    for command_input in inputs:
        display_value = 'N/A'
        
        if hasattr(command_input, 'expression'):
            display_value = command_input.expression
        
        elif hasattr(command_input, 'value'):
            display_value = command_input.value
            
        elif hasattr(command_input, 'valueOne'):
            display_value = f'\n    Value 1: {command_input.valueOne}'
            if hasattr(command_input, 'valueTwo'):
                display_value += f'\n    Value 2: {command_input.valueTwo}'
        
        elif hasattr(command_input, 'listItems'):
            display_value = command_input.selectedItem.name
        
        elif hasattr(command_input, 'isDirectionFlipped'):
            display_value = f'{command_input.isDirectionFlipped} (Is Direction Flipped?)'
            
        elif command_input.objectType == adsk.core.SelectionCommandInput.classType():
            selection = command_input.selection(0)
            selected_entity = selection.entity
            if selected_entity.objectType == adsk.fusion.ConstructionPlane.classType():
                display_value = f'A Construction Plane named: {selected_entity.name}'
            elif selected_entity.objectType == adsk.fusion.BRepFace.classType():
                parent_component_name = selected_entity.body.parentComponent.name
                display_value = f'A planar face from {parent_component_name}'

        futil.log(f'Name: {command_input.name}')
        futil.log(f'Type: {type(command_input).__name__}')
        futil.log(f'Input ID: {command_input.id}')
        futil.log(f'User Input: {display_value}')
        futil.log(seperator)

