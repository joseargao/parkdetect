from .base_processor import *
from .zone import Zone, read_zones_from_file, save_zone_to_file, remove_zone_from_file
from .mediaformat import *
from .colors import *
from .ymodel import YoloProcessor
from ..protocol import SerialHandler
from typing import List
from shapely import Point, Polygon


PERCENTAGE_ADJUSTMENT = 5
DRAG_ENABLE_RADIUS = 6


class InputProcessor(Processor):
    def __init__(self, obj_model: YoloProcessor, zone_model: YoloProcessor, plate_model: YoloProcessor,
                 zones: List[Zone], zones_cfg, enable_canvas, output_path, serial_handler: SerialHandler | None):
        super().__init__(zones=zones, obj_model=obj_model, zone_model=zone_model, plate_model=plate_model,
                         zones_cfg=zones_cfg, enable_canvas=enable_canvas, output_path=output_path,
                         serial_handler=serial_handler)

        if enable_canvas:
            self.event_handlers = {
                self.pygame.MOUSEBUTTONDOWN: self.handle_mousebuttondown,
                self.pygame.MOUSEBUTTONUP: self.handle_mousebuttonup,
                self.pygame.MOUSEMOTION: self.handle_mousemotion,
                self.pygame.KEYDOWN: self.handle_keydown,
            }

            self.key_handlers = {
                self.pygame.K_ESCAPE: self.handle_k_escape,
                self.pygame.K_RETURN: self.handle_k_return,
                self.pygame.K_UP: self.handle_k_up,
                self.pygame.K_DOWN: self.handle_k_down,
                self.pygame.K_c: self.handle_k_c,
                self.pygame.K_d: self.handle_k_mask,
                self.pygame.K_l: self.handle_k_mask,
                self.pygame.K_m: self.handle_k_m,
                self.pygame.K_o: self.handle_k_mask,
                self.pygame.K_s: self.handle_k_s,
                self.pygame.K_z: self.handle_k_mask,
            }

    def handle_event(self, event):
        ''' Handle pygame mouse and keyboard events

        @param  event    pygame event to be handled

        @return None '''

        if not self.pygame:
            return

        if event.type in self.event_handlers:
            self.event_handlers[event.type](event)

    def handle_mousebuttondown(self, event):
        click_pos = self.pygame.mouse.get_pos()
        if event.button == 1:
            if self.last_click_pos != click_pos and self.zone_setting:
                if self.drag_point is None:
                    self.zone_setting.add_point(click_pos)
                    self.set_zone_editing()
                else:
                    self.drag_enabled = True

            else:
                for zn in self.zones:
                    if zn.is_in_zone(click_pos):
                        self.zone_setting = zn
                        self.set_zone_editing()
                        break

            self.last_click_pos = click_pos

        elif event.button == 3:
            for trapezoid_points in self.trapezoids:
                trapezoid_poly = Polygon(trapezoid_points)
                if Point(click_pos).within(trapezoid_poly):
                    if not self.zone_setting:
                        self.zone_id = ""
                        self.canvas.draw_mode_text(f"Input Zone ID to set: {self.zone_id}")
                        self.pending_zone_points = trapezoid_points
                    break

    def handle_mousebuttonup(self, event):
        self.drag_enabled = False
        self.drag_point = None

    def handle_mousemotion(self, event):
        click_pos = self.pygame.mouse.get_pos()
        if self.zone_setting:
            if self.drag_enabled:
                self.zone_setting.update_point(self.drag_point, click_pos)
                self.drag_point = click_pos
            else:
                self.drag_point = None
                for zn_point in self.zone_setting.points:
                    circ = Point(zn_point).buffer(DRAG_ENABLE_RADIUS)
                    if circ.contains(Point(click_pos)):
                        self.drag_point = zn_point
                        break

    def handle_keydown(self, event):
        if event.key in range(self.pygame.K_0, self.pygame.K_9 + 1):
            self.handle_k_num(event)
        elif event.key in self.key_handlers:
            self.key_handlers[event.key](event)

    def handle_k_mask(self, event):
        mask_key = self.pygame.key.name(event.key)
        self.canvas.toggle_mask(mask_key)

    def handle_k_escape(self, event):
        self.zone_setting = None
        self.canvas.draw_mode_text(None)
        self.zone_id = ""
        self.pending_zone_points = []

    def handle_k_return(self, event):
        if not self.zone_setting and self.zone_id:
            self.canvas.draw_mode_text(f"Zone[{self.zone_id}: setting]")
            if self.pending_zone_points:
                self.zone_setting = Zone(zoneId=int(self.zone_id), points=self.pending_zone_points)
                self.pending_zone_points = []
            else:
                self.zone_setting = Zone(line=self.zone_id)
                for zone in self.zones:
                    if int(self.zone_id) == zone.zoneId:
                        self.zone_setting = zone
            self.zone_id = ""

    def handle_k_up(self, event):
        self.model.adjust_percentage(PERCENTAGE_ADJUSTMENT)

    def handle_k_down(self, event):
        self.model.adjust_percentage((-1) * PERCENTAGE_ADJUSTMENT)

    def handle_k_c(self, event):
        if self.zone_setting:
            self.zone_setting.points.clear()
            self.set_zone_editing()
        else:
            print(f"Total Count: {self.counter.get_count()}")
            for zone in self.zones:
                print(f"Zone {zone.zoneId}: {self.counter.get_count(zone_id=zone.zoneId)} vehicles parked")
            self.counter.reset_count()

    def handle_k_m(self, event):
        self.model = self.obj_model if self.model != self.obj_model else self.zone_model

    def handle_k_s(self, event):
        if self.zone_setting:
            if self.zone_setting.is_valid():
                save_zone_to_file(self.zones_file, self.zone_setting)
            else:
                remove_zone_from_file(self.zones_file, self.zone_setting.zoneId)

            self.zone_setting = None
            self.canvas.draw_mode_text(None)
            self.zones = read_zones_from_file(self.zones_file)

    def handle_k_num(self, event):
        zone_id = event.key - self.pygame.K_0
        if not self.zone_setting:
            if len(self.zone_id) < 3:
                self.zone_id = self.zone_id + str(zone_id)
                self.canvas.draw_mode_text(f"Input Zone ID to set: {self.zone_id}")
