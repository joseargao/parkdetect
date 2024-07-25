from shapely.geometry import Polygon, Point
from typing import List, Tuple

from .colors import *
from .ymodel import YoloDetection
from ..protocol import ZoneStatus, PwZoneState


ZONE_INERTIA_SECONDS = 3
MIN_ZONE_COVERAGE = 0.25


class Zone(ZoneStatus):
    def __init__(self, line=None, zoneId=None, points=None) -> None:
        if line:
            data = line.strip().split(",")
            points = [[int(data[i]), int(data[i + 1])] for i in range(0, len(data[:-1]), 2)]
            zoneId = int(data[-1])
        super().__init__(zoneId=zoneId, points=points, status=PwZoneState.Empty, count=0)
        self.polygon = self.__create_polygon(self.points)
        self.overlap = None
        self.inertia = 0
        self.license_plate = False

    def __create_polygon(self, points: List[Tuple[int]]):
        if len(points) < 3:
            return None

        return Polygon(points)

    def update_occupancy(self, detections: List[YoloDetection], fps=0) -> Tuple[bool, int]:
        ''' Check whether the zone is occupied or not

        @param detections    List of detected objects
        @param fps           Number of frames per second

        @return Tuple[changed, overlap_id]    bool changed:   determines if a change to zone occupancy has occured
                                              int overlap_id: if not None, then a new overlap_id has been entered
        '''

        valid_detections = [d for d in detections if not d.track or not d.moving]
        overlaps = [(self.polygon.intersection(detect.rectangle), detect.id) for detect in valid_detections]
        overlaps = [ovr for ovr in overlaps if ovr[0].area > 0]
        best_coverage = None
        self.overlap = None
        self.overlap_id = None
        changed = False
        if overlaps:
            best_coverage = max(overlaps, key=lambda ovr: ovr[0].area / self.polygon.area)
            if (best_coverage[0].area / self.polygon.area) > MIN_ZONE_COVERAGE:
                self.overlap = best_coverage[0]
                self.overlap_id = best_coverage[1]

        changed = self.update_occupancy_with_inertia(bool(self.overlap), fps=fps)

        if self.status is not PwZoneState.Occupied:
            self.license_plate = False

        return (changed, self.overlap_id)

    def update_occupancy_with_inertia(self, occupied, fps=0) -> bool:
        ''' Check whether the zone is occupied or not, taking inertia into account

        @param occupied      Boolean value based on whether there is enough overlap for occupancy
        @param fps           Number of frames per second

        @return True if a change in occupied status has occured '''

        overlapped = PwZoneState.Occupied if occupied else PwZoneState.Empty

        if self.status == overlapped:
            if self.inertia:
                self.inertia -= 1
        else:
            self.inertia += 1
            if self.inertia >= (ZONE_INERTIA_SECONDS * fps):
                self.status = overlapped
                self.inertia = 0
                return True

        return False

    def is_in_zone(self, point: Tuple[int, int]):
        p = Point(point)
        return p.within(self.polygon)

    def update_point(self, curr_point, new_point):
        self.points[self.points.index(curr_point)] = new_point

    def add_point(self, point):
        ''' Add a point to a possible new zone

        @param point    Coordinates of the point to be added

        @return None '''

        self.points.append(point)

    def get_length(self):
        ''' Get the number of points in the ZoneSetting object

        @param None

        @return Number of points in the ZoneSetting object '''

        return len(self.points)

    def is_valid(self):
        ''' Returns true if the saved points could be used to create a polygon

        @param None

        @return Boolean value of whether the saved points could be used to create a polygon '''

        return len(self.points) > 2

    def get_flat_coordinates(self):
        ''' Converts the saved point tuples into a combined flat list

        @param None

        @return Flat list containing all the saved point values '''

        return [pt for point in self.points for pt in point]


def read_zones_from_file(filename) -> List[Zone]:
    ''' Generate zone objects based on the zones config file

        @param filename  Path to the zones config file

        @return List of zone objects generated from the config file '''

    zones = []
    with open(filename, 'r') as file:
        for line in file:
            zones.append(Zone(line=line))
    return zones


def parse_zone(line):
    ''' Process a line from the zones config file

        @param line  One line from the zones config file

        @return The coordinates and zone number parsed from the line '''

    parts = line.strip().split(',')
    coordinates = list(map(int, parts[:-1]))
    zone_number = int(parts[-1])
    return coordinates, zone_number


def save_zone_to_file(filename, new_zone: Zone):
    ''' Add a new zone to the zones config file, or edit an existing zone

        @param filename  Path to the zones config file
        @param new_zone  Zone object corresponding to the zone that will be saved

        @return None '''

    zone = new_zone.get_flat_coordinates() + [new_zone.zoneId]
    str_zone = ','.join(map(str, zone)) + "\n"
    zones = read_zones_file(filename)

    update_zone(new_zone.zoneId, str_zone, zones)

    write_zones(filename, zones)


def write_zones(filename, zones):
    with open(filename, 'w') as file:
        file.writelines(zones)


def read_zones_file(filename):
    zones = []
    with open(filename, 'r') as file:
        zones = file.readlines()
    return zones


def update_zone(zoneId, str_zone, zones):
    match_found = False
    for i, zone in enumerate(zones):
        coordinates, zone_number = parse_zone(zone)
        if zone_number == zoneId:
            zones[i] = str_zone
            match_found = True

    if not match_found:
        zones.append(str_zone)


def remove_zone_from_file(filename, zoneId: int):
    zones = read_zones_file(filename)
    for line in zones:
        id = int(line.strip().split(',')[-1])
        if zoneId == id:
            zones.remove(line)
            break

    write_zones(filename, zones)
