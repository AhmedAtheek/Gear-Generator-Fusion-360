# Author: Ahmed Atheek Amir

from . import Cycloidal
from . import fusionAddInUtils as futil
import adsk.core


def run(context):
    try:
        if not context['IsApplicationStartup']:
            app = adsk.core.Application.get()
            ui = app.userInterface
    
        Cycloidal.start()
    except:
        futil.handle_error('run')


def stop(context):
    try:
        # Remove all of the event handlers your app has created
        futil.clear_handlers()

        # This will run the start function in each of your commands as defined in commands/__init__.py
        Cycloidal.stop()

    except:
        futil.handle_error('stop')