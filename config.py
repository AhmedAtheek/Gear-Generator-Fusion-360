import os

DEBUG = True

ADDIN_NAME = os.path.basename(os.path.dirname(__file__))

COMPANY_NAME = ""

# FIXME add good comments
design_workspace = 'FusionSolidEnvironment'
tools_tab_id = "ToolsTab"
my_tab_name = "Gear Generator"  # Only used if creating a custom Tab

my_panel_id = f'{ADDIN_NAME}_panel_2'
my_panel_name = ADDIN_NAME
my_panel_after = ''

