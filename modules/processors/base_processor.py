from abc import ABC, abstractmethod
import time
import cv2

from .zone import Zone
from .parkwatch_canvas import ParkWatchCanvas
from .mediaformat import *
from .colors import *
from .parkcounter import ParkCounter
from .ymodel import YoloDetection, YoloProcessor
from .trapezoid import find_best_fit_trapezoid
from ..protocol import SerialHandler, PwCommandCodes, PwZoneState
from datetime import datetime
from typing import List
from shapely import Point, Polygon


PERCENTAGE_ADJUSTMENT = 5
DRAG_ENABLE_RADIUS = 6


class Processor(ABC):
    def __init__(self, obj_model: YoloProcessor, zone_model: YoloProcessor, plate_model: YoloProcessor,
                 zones: List[Zone], zones_cfg, enable_canvas, output_path, serial_handler: SerialHandler | None):
        self.zones = zones
        self.zone_setting: Zone = None
        self.enable_canvas = enable_canvas
        self.zone_id = ""
        self.last_click_pos = None
        self.canvas = None
        self.zones_file = zones_cfg
        self.fps = 8.0
        self.pygame = None
        self.class_recorder = None
        self.counter = ParkCounter()
        self.serial_handler = serial_handler
        self.drag_point = None
        self.drag_enabled = False
        self.trapezoids: List[List[List[int, int]]] = []
        self.pending_zone_points = []

        self.model = obj_model
        self.obj_model = obj_model
        self.zone_model = zone_model
        self.plate_model = plate_model

        self.output_format = None
        self.output_path = output_path
        if self.output_path:
            self.output_format = parse_media_format(self.output_path)

        if enable_canvas:
            from .recorder import ScreenRecorder as class_recorder
            self.class_recorder = class_recorder

            import pygame as pygame
            self.pygame = pygame

    def handle_occupancy_change(self, zone):
        ''' Handle sending out occupancy change events

        @param  zone    zone that encurred the change

        @return None '''
        if self.serial_handler:
            self.serial_handler.send_command(PwCommandCodes.ZoneStatus, [zone])
            # HACK: transmission should be handled on a seperate thread of execution to avoid
            # this delay leaking out
            time.sleep(0.1)
        else:
            print(f"Zone {zone.zoneId}: {zone.status.name}")

    def next_operation(self):
        pass

    def set_zone_editing(self):
        point_cnt = self.zone_setting.get_length()
        if self.zone_setting.is_valid():
            self.canvas.draw_mode_text(f"Zone[{self.zone_setting.zoneId}: save {point_cnt} points?]")
        else:
            self.canvas.draw_mode_text(f"Zone[{self.zone_setting.zoneId}: {point_cnt} points.]")

    def merge_overlapping_polygons(self, polygons):
        num_polygons = len(polygons)
        merged_polygons = []
        while polygons:
            current_polygon = polygons.pop(0)
            overlaps = [i for i, poly in enumerate(polygons) if current_polygon.intersects(poly)]
            for overlap_index in overlaps[::-1]:
                union_polygon = current_polygon.union(polygons.pop(overlap_index))
                # Without this check, we sometimes get an unexpected MultiPolygon result of the union
                # How can this happen if they overlap? It's a mystery wrapped in an enigma.
                if union_polygon.geom_type == 'Polygon':
                    current_polygon = union_polygon
            merged_polygons.append(current_polygon)

        # Recursively merge overlapping polygons
        if len(merged_polygons) < num_polygons:
            return self.merge_overlapping_polygons(merged_polygons)

        return merged_polygons

    def draw_detections(self, source):
        detections: List[YoloDetection] = self.model.predict(source)

        self.trapezoids = []
        for detection in detections:
            if detection.mask is None:
                self.counter.add_vehicle(vehicle_id=detection.id)
                self.canvas.draw_detection(detection)
            else:
                trapezoid_points = None
                polygon_points = self.canvas.get_polygon_points(detection.mask)
                if len(polygon_points) >= 2:
                    trapezoid_points = find_best_fit_trapezoid(polygon_points)
                if trapezoid_points:
                    self.trapezoids.append(trapezoid_points)

        trapezoid_polygons = [Polygon(trapezoid) for trapezoid in self.trapezoids]
        merged_polygons = self.merge_overlapping_polygons(trapezoid_polygons)
        self.trapezoids = []
        for trap_poly in merged_polygons:
            trap_points = self.canvas.get_polygon_coords(trap_poly)
            trap_points = find_best_fit_trapezoid(trap_points)
            self.trapezoids.append(trap_points)
            self.canvas.draw_points(trap_points, color=BLUE, width=0)
            self.canvas.draw_points(trap_points, color=RED, width=2)

        for zone in self.zones:
            if zone.status == PwZoneState.Occupied and zone.license_plate == False:
                license_plates: List[YoloDetection] = self.plate_model.predict(source)
                for license_plate in license_plates:
                    self.save_cropped_image(zone, self.canvas.get_box_rect(license_plate.box))
                    zone.license_plate = True

            changed, parked_id = zone.update_occupancy(detections, self.fps)
            if parked_id:
                self.counter.add_vehicle(vehicle_id=parked_id, zone_id=zone.zoneId)
            if changed:
                self.handle_occupancy_change(zone)

            self.canvas.draw_zone(zone)

    def save_cropped_image(self, zone: Zone, rect):
        # Get current timestamp
        current_time = datetime.now()

        # Format timestamp (date_hours_minutes)
        timestamp_str = current_time.strftime("%Y%m%d_%H%M%S")

        # Format the filename
        screenshot_name = f"{zone.zoneId}_{timestamp_str}.png"

        # Extract the specified area as a subsurface
        cropped_surface = self.canvas.screen.subsurface(rect)

        # Save the subsurface as an image
        self.pygame.image.save(cropped_surface, screenshot_name)

    @abstractmethod
    def render(self):
        if self.zone_setting:
            color = get_color(number=self.zone_setting.zoneId)
            self.canvas.draw_points(self.zone_setting.points, width=2, color=color,
                                    drag_point=self.drag_point, point_radius=DRAG_ENABLE_RADIUS)

        if self.pending_zone_points:
            self.canvas.draw_points(self.pending_zone_points, width=5)

    @abstractmethod
    def finalize(self):
        pass
