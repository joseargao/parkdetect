from shapely.geometry import Polygon
from cv2.typing import MatLike
from typing import Tuple, List

from .ymodel import YoloDetection
from .colors import *
from .zone import Zone


class Canvas():
    def __init__(self, width, height, caption, enabled=True, graphics_mask="zod") -> None:
        self.mode_text = None
        self.width = width
        self.height = height
        self.recording = False
        self.dot_size = 10
        self.dot_pad = 5
        self.graphics_mask = graphics_mask

        self.pygame = None
        self.enabled = enabled
        if self.enabled:
            import pygame as pygame
            self.pygame = pygame
            self.pygame.init()

            self.screen = pygame.display.set_mode((width, height))
            pygame.display.set_caption(caption)
            self.cap_font = pygame.font.SysFont(None, 40)
            self.sub_font = pygame.font.SysFont(None, 32)
            pygame.display.flip()

    def draw_image(self, image_path: str):
        '''Draw an image on the canvas

        @param  image_path      Path to the image file

        @return None '''

        if not self.enabled:
            return

        image = self.pygame.image.load(image_path)
        self.screen.blit(image, (0, 0))

    def draw_frame(self, frame: MatLike):
        '''Draw a frame from a stream or video on the canvas

        @param  frame      A frame of video to be displayed on the canvas

        @return None '''

        if not self.enabled:
            return

        image = self.pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "BGR")
        self.screen.blit(image, (0, 0))

    def draw_pos(self, pos: Tuple[int, int]):
        '''Write the coordinates of a specific position on the canvas

        @param  pos      The x and y coordinates to be drawn onto the canvas

        @return None '''

        if not self.enabled:
            return

        if pos:
            self.write_text(f"({pos[0]},{pos[1]})", self.cap_font, pos, YELLOW, self.screen, background=BLACK)

    def draw_points(self, points: List[Tuple[int, int]], width: int = 1,
                    color: Tuple[int, int, int] = BLACK, drag_point=None, point_radius=2):
        '''Draw circles at specific positions on the canvas, and draw a polygon illustrating a possible zone
        area using those points

        @param  points       The x and y coordinates of a point on the canvas
        @param  width        The width of lines for the polygon, as well as radius of the circles
        @param  color        The color of the polygon to be drawn
        @param  drag_point   The x and y coordinates of a point that will be used for dragging
        @param  point_radius The radius of the circles which will be drawn

        @return None '''

        if not self.enabled:
            return

        if len(points) > 1:
            self.pygame.draw.polygon(self.screen, color, points, width=width)
        for point in points:
            if point == drag_point:
                self.pygame.draw.circle(self.screen, MAGENTA, point, point_radius)
            else:
                self.pygame.draw.circle(self.screen, color, point, point_radius)

    def draw_recording_icon(self, enable: bool):
        '''Toggle whether a recording icon should be shown on the canvas

        @param  enable    True to show a recording icon or False to hide it

        @return None '''

        self.recording = enable

    def render(self):
        '''Render the recording icon and/or the mode text on the canvas

        @param  None

        @return None '''

        if not self.enabled:
            return

        if self.mode_text:
            self.write_text(self.mode_text, self.cap_font,
                            ((self.dot_size + self.dot_pad) * 2, self.height),
                            YELLOW, self.screen, background=BLACK)
        if self.recording:
            self.pygame.draw.circle(self.screen, RED,
                                    (self.dot_size + self.dot_pad, self.height - (self.dot_size + self.dot_pad)),
                                    self.dot_size)
        self.pygame.display.flip()

    def save_image(self, output_path: str):
        '''Save the image data on the canvas to the provided path

        @param  output_path    Path where the image will be saved

        @return None '''

        if not self.enabled:
            return

        self.pygame.image.save(self.screen, output_path)

    def get_box_rect(self, box: List[int]):
        '''Create a rectangle object as defined by the points

        @param  box    List of points in xyxy format

        @return None '''

        return self.pygame.Rect(int(box[0]), int(box[1]), int(box[2] - box[0]), int(box[3] - box[1]))

    def get_polygon_points(self, mask: List[List[int]]):
        '''Create a list of points defined by the mask

        @param  box    List of points in xy format

        @return List of points '''

        return [[int(p[0]), int(p[1])] for p in mask]

    def get_box_caption(self, box: List[int]):
        '''Get the coordinates where a caption for a box object should be displayed

        @param  box    List of points in xyxy format

        @return  Coordinates of where the box caption should be displayed'''

        return (int(box[0]), int(box[1]))

    def get_polygon_coords(self, poly: Polygon):
        '''Get the coordinates of a polygon object

        @param  poly    The polygon whose coordinates are being requested

        @return Coordinates of the provided polygon object '''

        return [(int(x), int(y)) for x, y in poly.exterior.coords]

    def write_text(self, text, font, top_left, color, screen, background=None):
        '''Write some text onto the canvas

        @param  text       Text to be written
        @param  font       Font to be used for the text
        @param  top_left   coordinates at the top-left of the canvas
        @param  color      Color of the text to be written
        @param  screen     The canvas being written onto
        @param  background The background color of the text

        @return None '''

        if not self.enabled:
            return

        # Render the text
        text_surface = font.render(text, True, color, background)

        # Calculate the position for the text
        text_rect: self.pygame.Rect = text_surface.get_rect()
        text_rect.bottomleft = top_left

        # Blit the text onto the screen
        screen.blit(text_surface, text_rect)
