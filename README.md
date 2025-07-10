# Gear-Generator-Fusion-360
Gear Generator for fusion 360

- Written in python, custom fusion 360 script to generate gears based on given parameters
- Currently only creates cycloidal gears
- More gear types to be added in the future

## How to install
clone the repo to]

Windows – %appdata%\Autodesk\Autodesk Fusion 360\API\Scripts\
Mac – $HOME/Library/Application Support/Autodesk/Autodesk Fusion 360/API/Scripts\

## Paramaters
<img width="316" height="307" alt="image" src="https://github.com/user-attachments/assets/df1835f0-19a5-4c16-a012-ca0d64a50c9b" />

### Gear ratio:
  - gear ratio = 1 - No of rollers/pins
  - So No of rollers = gear ratio + 1

### Eccentricity:
  - Difference between centor of ring pin pitch ring and centor of cycloidal gear.

### Rotor Radius:
  - The radius of the circle where the rollers/pins lie

### Center Hole Radius:
  - The radius of central hole for the shaft

### Points per tooth:
  - The sampling of the points
  - Use a higher value for greater accuracy

Formulas for curve:
[https://blogs.solidworks.com/teacher/2014/07/building-a-cycloidal-drive-with-solidworks.html](url)
