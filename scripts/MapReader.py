import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageColor, ImageFont # https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html
import math

PLAY_AREA_FIRST_ROW = 3
PLAY_AREA_LAST_ROW = 20

MAP_START_OFFSET = 8
BYTES_PER_HEX = 5 # Two bytes for column, two bytes for row, one byte for hex type.

SUPPORTED_FORMAT_VERSION = 9 # For version six, will render map but not read control point or unit data.

IMAGE_HEX_RADIUS = 64
IMAGE_HEX_RADIUS_OUTSIDE_PLAY_AREA = 32+16
IMAGE_HEX_RADIUS_CONTROL_POINT = 32+16+8

IMAGE_HEX_ANGLE = 30
IMAGE_HEX_HALFWIDTH = math.cos(math.radians(IMAGE_HEX_ANGLE)) * IMAGE_HEX_RADIUS
IMAGE_HEX_SIDE_LENGTH = 2 * math.sin(math.radians(IMAGE_HEX_ANGLE)) * IMAGE_HEX_RADIUS

IMAGE_BACKGROUND_COLOR = (255,255,255,0)

FONT_NAME = "ariblk.ttf"
FONT_SIZE = 24

DEFAULT_HEX_FILL_COLOR = 'white'
HEX_TYPE_TO_FILL_COLOR = {
    0: 'lime', # Grass
    1: 'green', # Forest
    2: 'navy', # Water with red smoke
    3: 'gray', # Road
    4: 'blue', # Water
    5: 'khaki', # Bare ground
    6: 'olive', # Path through forest
    7: 'purple' # Gate generator
}

def isEven(value):
    return value % 2 == 0

def getHexPixelCoordinates(hexCol, hexRow, hexXOffset, rowCount):
    x = hexCol + hexRow/2 + hexXOffset
    y = rowCount - 1 - (hexRow - minHexRow)

    pixelX = IMAGE_HEX_HALFWIDTH + x*2*IMAGE_HEX_HALFWIDTH
    pixelY = IMAGE_HEX_RADIUS + y*(0.5*IMAGE_HEX_SIDE_LENGTH + IMAGE_HEX_RADIUS)

    return (pixelX, pixelY)

def isHexInPlayArea(hexCol, hexRow):
    firstColInPlayArea = 4 - math.ceil(hexRow/2)
    lastColInPlayArea = firstColInPlayArea + (21 if isEven(hexRow) else 22) - 1
    isInPlayArea = (hexRow >= PLAY_AREA_FIRST_ROW and hexRow <= PLAY_AREA_LAST_ROW) and (hexCol >= firstColInPlayArea and hexCol <= lastColInPlayArea)
    return isInPlayArea

def getFillColorForHexType(hexType):
    return HEX_TYPE_TO_FILL_COLOR.get(hexType, DEFAULT_HEX_FILL_COLOR)

basePath = 'C:/Program Files (x86)/Steam/steamapps/common/Möbius Front \'83/Content/maps/'

files = [item for item in os.listdir(basePath) if os.path.isfile(os.path.join(basePath, item))]

font = ImageFont.truetype(FONT_NAME, FONT_SIZE)

for filePath in files:

    filePath = basePath + filePath
    
    with open(filePath, 'rb') as file:
        data = file.read()

    formatVersion = int.from_bytes(data[0:4], byteorder='little')
    hexCount = int.from_bytes(data[4:8], byteorder='little')

    print('='*64)
    print(f'File: {filePath}')
    print(f'Format version: {formatVersion}')
    print(f'Hex count: {hexCount}')

    hexes = [] # List of tuples: (col, row, type, number); number is order in file.
    controlPoints = [] # List of tuples: (col, row).
    alliedUnits = [] # List of tuples: (col, row, unit type).
    enemyUnits = [] # List of tuples: (col, row, unit type).

    hexNumber = 0

    maxHexRow = -999
    minHexRow = 999

    # Measured in hex widths.
    maxHexX = -999
    minHexX = 999

    # Read hex data.
    for hexIndex in range(MAP_START_OFFSET, MAP_START_OFFSET + hexCount * BYTES_PER_HEX, BYTES_PER_HEX):
        hexCol = int.from_bytes(data[hexIndex:hexIndex+2], byteorder='little', signed=True)
        hexRow = int.from_bytes(data[hexIndex+2:hexIndex+4], byteorder='little', signed=True)
        hexType = int.from_bytes(data[hexIndex+4:hexIndex+5], byteorder='little')

        hexes.append((hexCol, hexRow, hexType, hexNumber))
        hexNumber = hexNumber + 1

        maxHexRow = max(maxHexRow, hexRow)
        minHexRow = min(minHexRow, hexRow)

        x = hexCol + hexRow/2

        maxHexX = max(maxHexX, x)
        minHexX = min(minHexX, x)
    
    rowCount = maxHexRow - minHexRow + 1
    hexXOffset = -minHexX

    # Read control point and unit data.
    if formatVersion == SUPPORTED_FORMAT_VERSION:
        firstByteAfterHexData = 8 + BYTES_PER_HEX * hexCount
        unknown = int.from_bytes(data[firstByteAfterHexData:firstByteAfterHexData+4], byteorder='little', signed=True)

        offsetC2 = firstByteAfterHexData + 4
        controlPointCount = int.from_bytes(data[offsetC2:offsetC2+4], byteorder='little', signed=True)

        for cpIndex in range(0, controlPointCount):
            offset = offsetC2 + 4 + cpIndex*4
            hexCol = int.from_bytes(data[offset:offset+2], byteorder='little', signed=True)
            hexRow = int.from_bytes(data[offset+2:offset+4], byteorder='little', signed=True)

            controlPoints.append((hexCol, hexRow))

        offsetC3 = offsetC2 + 4 + controlPointCount * 4
        alliedUnitCount = int.from_bytes(data[offsetC3:offsetC3+4], byteorder='little', signed=True)

        for auIndex in range(0, alliedUnitCount):
            offset = offsetC3 + 4 + auIndex*5
            hexCol = int.from_bytes(data[offset:offset+2], byteorder='little', signed=True)
            hexRow = int.from_bytes(data[offset+2:offset+4], byteorder='little', signed=True)
            unitType = int.from_bytes(data[offset+4:offset+5], byteorder='little', signed=True)

            alliedUnits.append((hexCol, hexRow, unitType))

        offsetC4 = offsetC3 + 4 + alliedUnitCount * 5
        enemyUnitCount = int.from_bytes(data[offsetC4:offsetC4+4], byteorder='little', signed=True)

        for euIndex in range(0, enemyUnitCount):
            offset = offsetC4 + 4 + euIndex*5
            hexCol = int.from_bytes(data[offset:offset+2], byteorder='little', signed=True)
            hexRow = int.from_bytes(data[offset+2:offset+4], byteorder='little', signed=True)
            unitType = int.from_bytes(data[offset+4:offset+5], byteorder='little', signed=True)

            enemyUnits.append((hexCol, hexRow, unitType))
        
        print(f'Unknown value: {unknown}')
        print(f'Number of control points: {controlPointCount}')
        print(f'Number of allied units: {alliedUnitCount}')
        print(f'Number of enemy units: {enemyUnitCount}')

    # Draw map.

    imageWidth = math.ceil((maxHexX - minHexX + 1) * 2*IMAGE_HEX_HALFWIDTH)
    imageHeight = math.ceil(2*IMAGE_HEX_RADIUS + (rowCount-1)*(IMAGE_HEX_SIDE_LENGTH + IMAGE_HEX_RADIUS - IMAGE_HEX_SIDE_LENGTH/2))
    
    imageMap = Image.new('RGBA', (imageWidth, imageHeight), color = IMAGE_BACKGROUND_COLOR)
    draw = ImageDraw.Draw(imageMap)

    # Use the undocumented "fontmode" member to get aliased text
    # Modes are documented here: https://pillow.readthedocs.io/en/stable/handbook/concepts.html#concept-modes
    # Sources:
    # https://stackoverflow.com/a/62813181/2274765
    # https://stackoverflow.com/a/5747805/2274765
    # https://mail.python.org/pipermail/image-sig/2005-August/003497.html
    draw.fontmode = "1"
    
    for hex in hexes:
        hexCol = hex[0]
        hexRow = hex[1]
        hexType = hex[2]
        hexNumber = hex[3]

        pixelCoords = getHexPixelCoordinates(hexCol, hexRow, hexXOffset, rowCount)
        hexX = pixelCoords[0]
        hexY = pixelCoords[1]

        fillColor = getFillColorForHexType(hexType)

        # Too hard to distinguish dark grass hexes from regular forest hexes unless the former is really dark.
        #if (not isInPlayArea):
            #fillColor = tuple(math.floor(val/3) for val in ImageColor.getrgb(fillColor))

        isInPlayArea = isHexInPlayArea(hexCol, hexRow)

        if isInPlayArea:
            draw.regular_polygon(((hexX, hexY), IMAGE_HEX_RADIUS), 6, IMAGE_HEX_ANGLE, fill = fillColor, outline = 'black')
        else:
            draw.regular_polygon(((hexX, hexY), IMAGE_HEX_RADIUS), 6, IMAGE_HEX_ANGLE, fill = 'black', outline = 'black')
            draw.regular_polygon(((hexX, hexY), IMAGE_HEX_RADIUS_OUTSIDE_PLAY_AREA), 6, IMAGE_HEX_ANGLE, fill = fillColor, outline = 'black')
        
        draw.text((hexX, hexY), f"{hexCol}, {hexRow}", font=font, anchor="mm")
        draw.text((hexX, hexY + IMAGE_HEX_SIDE_LENGTH/2), f"{hexNumber}", font=font, anchor="mm")

    if formatVersion == SUPPORTED_FORMAT_VERSION:

        for controlPoint in controlPoints:
            hexCol = controlPoint[0]
            hexRow = controlPoint[1]

            pixelCoords = getHexPixelCoordinates(hexCol, hexRow, hexXOffset, rowCount)
            hexX = pixelCoords[0]
            hexY = pixelCoords[1]

            # Unfortunately, regular_polygon() doesn't support variable line width.
            # If it did, these hexagons would be drawn with a thicker line to enhance their visibility.
            draw.regular_polygon(((hexX, hexY), IMAGE_HEX_RADIUS_CONTROL_POINT), 6, IMAGE_HEX_ANGLE, fill = None, outline = 'red')
        
        for alliedUnit in alliedUnits:
            hexCol = alliedUnit[0]
            hexRow = alliedUnit[1]
            unitType = alliedUnit[2]

            pixelCoords = getHexPixelCoordinates(hexCol, hexRow, hexXOffset, rowCount)
            hexX = pixelCoords[0]
            hexY = pixelCoords[1]

            draw.text((hexX, hexY - IMAGE_HEX_SIDE_LENGTH/2), f"{unitType}", font=font, anchor="mm", fill='blue')
        
        for enemyUnit in enemyUnits:
            hexCol = enemyUnit[0]
            hexRow = enemyUnit[1]
            unitType = enemyUnit[2]

            pixelCoords = getHexPixelCoordinates(hexCol, hexRow, hexXOffset, rowCount)
            hexX = pixelCoords[0]
            hexY = pixelCoords[1]

            draw.text((hexX, hexY - IMAGE_HEX_SIDE_LENGTH/2), f"{unitType}", font=font, anchor="mm", fill='red')
    
    # Save map.
    scriptPath = os.path.dirname(os.path.realpath(sys.argv[0]))
    inFile = Path(filePath).stem
    outName = scriptPath + "/" + inFile + "-map.png"
    imageMap.save(outName, "PNG")
