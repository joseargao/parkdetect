# Define colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
TEAL = (0, 128, 128)
BROWN = (165, 42, 42)
PINK = (255, 192, 203)
GRAY = (128, 128, 128)
LIME = (0, 255, 0)
NAVY = (0, 0, 128)

TRANSPARENT = (0, 0, 0, 255)
NON_TRANSPARENT = (255, 255, 255, 255)

COLORS = [
    WHITE,
    RED,
    GREEN,
    BLUE,
    YELLOW,
    CYAN,
    MAGENTA,
    ORANGE,
    PURPLE,
    TEAL,
    BROWN,
    PINK,
    GRAY,
    LIME,
    NAVY
]

used_colors = set()

# Dictionary to store box colors associated with ID numbers
box_colors = {}


def get_color(number: int):
    ''' Get a color by index

    @param  number    Index of the color being requested

    @return RGB values for the retrieved color '''

    colors = [RED, GREEN, CYAN, TEAL, BLUE, MAGENTA, BROWN]
    return colors[(number - 1) % len(colors)]


def get_box_color():
    ''' Get an unused color from COLORS

    @param  None

    @return RGB values for the retrieved color '''

    for color in COLORS:
        if color not in used_colors:
            used_colors.add(color)
            return color
    # If all colors are used, return black
    return (255, 255, 255)
