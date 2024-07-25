from ultralytics import YOLO, engine
from typing import List
from shapely.geometry import Polygon
from collections import defaultdict
from collections import deque


MOTION_TRACKING_LIMIT = 60
MOTION_DISTANCE_THRESHOLD = 30
detected_objects = defaultdict(lambda: LimitedSizeList(MOTION_TRACKING_LIMIT))


class LimitedSizeList(deque):
    def __init__(self, size_limit):
        super().__init__(maxlen=size_limit)

    def append(self, item):
        ''' Append an item to the limited size list. Remove the oldest item if there is
        no more space available

        @param item    The item to be appended to the list

        @return None '''

        if len(self) == self.maxlen:
            self.popleft()  # Remove the oldest entry when the limit is reached
        super().append(item)


class YoloDetection():
    def __init__(self, type, id, name, score, box, mask, track=False) -> None:
        self.type = type
        self.id = id
        self.name = name
        self.score = score
        self.box = box
        self.rectangle = self.__create_rectangle(self.box)
        self.moving = self.detect_movement()
        self.track = track
        self.mask = mask

    def detect_movement(self):
        ''' Determine whether a tracked object is moving

        @param None

        @return Boolean value of whether the tracked object was moving '''

        detected_objects[self.id].append(self.rectangle.centroid)
        recent_positions = detected_objects[self.id]
        if len(recent_positions) > 1:
            max_distance = max([recent_positions[0].distance(p) for p in recent_positions])
            return max_distance > MOTION_DISTANCE_THRESHOLD
        return False

    def __create_rectangle(self, points: List[int]):
        if len(points) != 4:
            raise ValueError(f"incorect box geometry specified: {len(points)}")

        return Polygon([(points[0], points[1]), (points[0], points[3]),
                        (points[2], points[3]), (points[2], points[1]),])


class YoloProcessor():
    def __init__(self, model_name, imgsz, track, percentage, allow) -> None:
        self.imgsz = imgsz
        self.model = YOLO(model_name)
        self.track = track
        self.percentage = percentage
        self.allow = [int(a) for a in allow.split(',')] if allow is not None else []
        print(f"{self.allow}")

    def __validate_percentage(self):
        if self.percentage > 100:
            self.percentage = 100
        if self.percentage < 0:
            self.percentage = 0
        print(f"Current detection threshold: {self.percentage}")

    def adjust_percentage(self, adjustment):
        self.percentage += adjustment
        self.__validate_percentage()

    def update_percentage(self, update):
        self.percentage = update
        self.__validate_percentage()

    def predict(self, source) -> List[YoloDetection]:
        ''' Perform object detection and/or tracking on the source media

        @param source    The source image path or video/stream frame

        @return List of detected objects '''

        if self.track:
            results = self.model.track(source, verbose=False, imgsz=self.imgsz, persist=True,
                                       conf=self.percentage / 100.0)
        else:
            results = self.model.predict(source, verbose=False, imgsz=self.imgsz, conf=self.percentage / 100.0)
        detections = []
        for result in results:
            for i, cls in enumerate(result.boxes.cls):
                type = int(cls)
                if type not in self.allow:
                    continue
                id = int(result.boxes.id[i]) if result.boxes.id is not None else 0
                name = result.names[type]
                score = result.boxes.conf[i]
                box = result.boxes.xyxy[i]
                mask = result.masks.xy[i] if result.masks else None
                detections.append(YoloDetection(type, id, name, score, box, mask, self.track))
        return detections
