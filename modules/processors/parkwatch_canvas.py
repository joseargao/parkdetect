from shapely.geometry import Polygon
from cv2.typing import MatLike
from typing import Tuple, List

from .ymodel import YoloDetection
from .colors import *
from .zone import Zone
from .base_canvas import Canvas
from ..protocol import PwZoneState
from .trapezoid import find_best_fit_trapezoid


class ParkWatchCanvas(Canvas):
    def __init__(self, width, height, caption, enabled=True, graphics_mask="zod") -> None:
        super().__init__(width, height, caption, enabled, graphics_mask)
        if self.enabled:
            self.hash_surface = self.__create_hash(spacing=16, width=2)

    def __create_hash(self, spacing: int, width: int):
        if not self.enabled:
            return

        self.hash_width = width
        hash_surface = self.pygame.Surface((self.width, self.height), self.pygame.SRCALPHA)
        hash_surface.fill(TRANSPARENT)
        hash_surface.set_colorkey(TRANSPARENT)
        for x in range(0, self.width, spacing):
            self.pygame.draw.line(hash_surface, NON_TRANSPARENT, (x, 0), (self.width + x, self.height), width)
            self.pygame.draw.line(hash_surface, NON_TRANSPARENT, (-x, 0), (self.width - x, self.height), width)

        return hash_surface

    def draw_detection(self, detection: YoloDetection):
        '''Draw a box corresponding to a detected object on the canvas

        @param  detection      An object that was detected by the YOLO model

        @return None '''

        if not self.enabled or "d" not in self.graphics_mask.lower():
            return

        color = RED if detection.moving and detection.id != 0 else ORANGE
        self.pygame.draw.rect(self.screen, color, self.get_box_rect(detection.box), 2)
        pos = self.get_box_caption(detection.box)
        label = f"{detection.name}[{detection.id}]" if detection.id != 0 else f"{detection.name}"
        if "l" in self.graphics_mask.lower():
            self.write_text(f"{label}: {detection.score:.0%} {detection.type}", self.cap_font, pos, color, self.screen)

    def draw_zone(self, zone: Zone):
        '''Draw a box corresponding to an occupancy zone on the canvas

        @param  zone      An object corresponding to an area that may be occupied or not

        @return None '''

        if not self.enabled or "z" not in self.graphics_mask.lower():
            return

        if zone.is_valid():
            color = get_color(zone.zoneId)
            self.draw_zone_overlap(zone)
            self.pygame.draw.polygon(self.screen, color, zone.points,
                                     width=8 if zone.status == PwZoneState.Occupied else 2)
            self.write_text(f"{zone.zoneId}", self.sub_font, self.__get_label_position(zone.points), color, self.screen)

    def draw_zone_overlap(self, zone: Zone):
        '''Draw a hash corresponding to the area of overlap between a zone and a detected object on the canvas

        @param  zone      An object corresponding to an area that may be occupied or not

        @return None '''

        if not self.enabled or "o" not in self.graphics_mask.lower():
            return

        if zone.overlap:
            cutout_polygon = self.get_polygon_coords(zone.overlap)
            cutout_surface = self.pygame.Surface((self.width, self.height), self.pygame.SRCALPHA)
            cutout_surface.fill(TRANSPARENT)
            cutout_surface.set_colorkey(TRANSPARENT)
            self.pygame.draw.polygon(cutout_surface, NON_TRANSPARENT, cutout_polygon)
            hash_surface = self.hash_surface.copy()
            self.pygame.draw.polygon(hash_surface, NON_TRANSPARENT, cutout_polygon, self.hash_width)

            cutout_mask = self.pygame.mask.from_surface(cutout_surface)
            hash_mask = self.pygame.mask.from_surface(hash_surface)

            overlap_mask = hash_mask.overlap_mask(cutout_mask, (0, 0))
            overlap_surf = overlap_mask.to_surface(setcolor=GRAY)
            overlap_surf.set_colorkey(TRANSPARENT)

            self.screen.blit(overlap_surf, (0, 0))

    def draw_mode_text(self, text: str):
        '''Update the mode text that will be displayed on the canvas

        @param  text      Mode text to be displayed on the canvas

        @return None '''

        self.mode_text = text

    def __get_label_position(self, points: List[Tuple[int, int]]):
        bottom = max(points, key=lambda t: t[1])[1]
        bottom += self.sub_font.get_height()
        if bottom > self.height:
            bottom = self.height
        right = max(points, key=lambda t: t[0])[0]
        left = min(points, key=lambda t: t[0])[0]
        return (left + ((right - left) / 2), bottom)

    def toggle_mask(self, mask: str):
        '''Toggle display of zone, overlap, or detection boxes

        @param  mask    Must be one of the following characters:
        @               z: denoting zones
        @               o: denoting overlaps
        @               d: denoting detection boxes
        @               l: denoting detection box labels

        @return None '''

        if len(mask) > 1:
            return

        if mask in self.graphics_mask.lower():
            self.graphics_mask = ''.join([c for c in self.graphics_mask if c != mask])
        else:
            self.graphics_mask = self.graphics_mask + mask
