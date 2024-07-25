from typing import List

from .input_processor import *
from .ymodel import YoloProcessor
from .zone import Zone


class ImageProcessor(InputProcessor):
    def __init__(self, input_path, model: YoloProcessor, zone_model: YoloProcessor, plate_model: YoloProcessor,
                 zones: List[Zone], zones_cfg, enable_canvas, output_path, graphics_mask, serial_handler) -> None:
        super().__init__(zones=zones, obj_model=model, zone_model=zone_model, plate_model=plate_model,
                         zones_cfg=zones_cfg, enable_canvas=enable_canvas, output_path=output_path,
                         serial_handler=serial_handler)

        self.zones = zones
        self.input_path = input_path
        self.screen_width, self.screen_height = self.get_image_dimensions(input_path)
        self.canvas = ParkWatchCanvas(self.screen_width,
                                      self.screen_height,
                                      "Park Detect",
                                      enable_canvas,
                                      graphics_mask)
        self.output_path = output_path

        if enable_canvas:
            self.stream_handlers = {
                self.pygame.K_r: self.handle_k_r,
            }

            self.key_handlers.update(self.stream_handlers)

    def get_image_dimensions(self, image_path):
        ''' Retrieve the height and width of an image

        @param  image_path    Path to the image file

        @return A (width, height) tuple '''

        img = cv2.imread(image_path)
        if img is None:
            return 1280, 720
        height, width, _ = img.shape
        return width, height

    def render(self):
        ''' Render the processed image onto the canvas

        @param  None

        @return None '''

        self.canvas.draw_image(self.input_path)

        self.draw_detections(self.input_path)

        super().render()
        self.canvas.render()

    def finalize(self):
        pass

    def handle_k_r(self, event):
        if self.output_format == MediaFormat.IMAGE:
            self.canvas.save_image(output_path=self.output_path)
