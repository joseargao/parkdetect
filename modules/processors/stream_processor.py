from typing import List
from datetime import datetime, timedelta
import subprocess

from .input_processor import *
from .ymodel import YoloProcessor
from .zone import Zone
from .vidbuff import BufferlessVideoCapture


class FreezeType(Enum):
    NOMINAL = 0
    FREEZE_NEXT = 1
    FROZEN = 2


class StreamProcessor(InputProcessor):
    def __init__(self, input_path, input_format, model: YoloProcessor, zone_model: YoloProcessor, plate_model: YoloProcessor,  # noqa
                 zones: List[Zone], zones_cfg, enable_canvas, output_path, graphics_mask, serial_handler, auto_record) -> None:  # noqa
        super().__init__(zones=zones, obj_model=model, zone_model=zone_model, plate_model=plate_model,
                         zones_cfg=zones_cfg, enable_canvas=enable_canvas, output_path=output_path,
                         serial_handler=serial_handler)

        self.zones = zones
        self.input_path = input_path
        self.input_format = input_format
        self.freeze_frame = FreezeType.NOMINAL

        self.cap = BufferlessVideoCapture(self.input_path, self.input_format == MediaFormat.VIDEO)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.screen_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.screen_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.canvas = ParkWatchCanvas(self.screen_width,
                                      self.screen_height,
                                      "Park Detect",
                                      enable_canvas,
                                      graphics_mask)

        self.recorder = None
        self.ffmpeg_process = None
        if self.output_format == MediaFormat.STREAM:
            self.ffmpeg_process = self.open_ffmpeg_stream_process(self.output_path)

        self.last_update = datetime.now()
        self.frame_count = 0

        if enable_canvas:
            self.stream_handlers = {
                self.pygame.K_f: self.handle_k_f,
                self.pygame.K_p: self.handle_k_p,
                self.pygame.K_r: self.handle_k_r,
            }

            self.key_handlers.update(self.stream_handlers)

        self.auto_record_start = None
        if auto_record:
            self.auto_record_start = datetime.now() + timedelta(seconds=auto_record)

    def open_ffmpeg_stream_process(self, output_stream: str):
        ''' Open FFMPEG output stream

        @param  output_stream    FFMPEG output stream

        @return A Popen object representing a running process '''

        args = [
            "ffmpeg", "-stream_loop", "-1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s",
            f"{self.screen_width}x{self.screen_height}", "-i", "pipe:0", "-pix_fmt", "yuv420p",
            "-rtsp_transport", "tcp", "-f", "rtsp", f"{output_stream}"
        ]
        return subprocess.Popen(args, stdin=subprocess.PIPE)

    def render(self):
        ''' Render the processed stream frame onto the canvas

        @param  None

        @return None '''

        self.update_fps()

        if self.auto_record_start and datetime.now() > self.auto_record_start:
            self.handle_k_r(None)
            self.auto_record_start = None

        if self.freeze_frame != FreezeType.FROZEN:
            self.__frame = self.cap.read()

            if self.freeze_frame == FreezeType.FREEZE_NEXT:
                self.freeze_frame = FreezeType.FROZEN

        if self.__frame is not None:
            self.canvas.draw_frame(self.__frame)

            self.draw_detections(self.__frame)

            super().render()
            self.canvas.render()

            if self.recorder:
                self.recorder.capture_frame(self.canvas.screen)

            if self.ffmpeg_process:
                self.__frame = cv2.rotate(self.pygame.surfarray.pixels3d(self.canvas.screen), cv2.ROTATE_90_CLOCKWISE)
                self.__frame = cv2.flip(self.__frame, 1)
                self.ffmpeg_process.stdin.write(self.__frame.tobytes())

    def update_fps(self):
        ''' Calculate the FPS value for the stream

        @param  None

        @return None '''

        self.frame_count += 1
        total_seconds = (datetime.now() - self.last_update).total_seconds()
        if total_seconds > 1.0:
            self.fps = self.frame_count / total_seconds
            self.frame_count = 0
            self.last_update = datetime.now()

    def finalize(self):
        ''' Close the stream and save any ongoing recordings

        @param  None

        @return None '''

        self.cap.release()
        if self.recorder:
            self.recorder.end_recording()
        if self.ffmpeg_process:
            self.ffmpeg_process.stdin.close()
            self.ffmpeg_process.wait()

    def handle_k_f(self, event):
        self.freeze_next_operation()

    def handle_k_p(self, event):
        self.play_operation()

    def handle_k_r(self, event):
        if self.output_format == MediaFormat.VIDEO:
            if self.recorder:
                self.canvas.draw_recording_icon(False)
                self.recorder.end_recording()
                self.recorder = None
            else:
                self.canvas.draw_recording_icon(True)
                self.recorder = self.class_recorder(self.screen_width,
                                                            self.screen_height,
                                                            self.fps,
                                                            out_file=self.output_path)

    def freeze_next_operation(self):
        self.freeze_frame = FreezeType.FREEZE_NEXT

    def play_operation(self):
        self.freeze_frame = FreezeType.NOMINAL
