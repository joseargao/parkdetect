import cv2
import queue
import threading
import time


class BufferlessVideoCapture:
    """reads frames in background and only provides a get to the latest frame """

    def __init__(self, input_path, is_video: bool):
        self.input_path = input_path

        self.cap = cv2.VideoCapture(input_path)
        if not self.cap.isOpened():
            raise RuntimeError(f"Unable to open {self.input_path}")

        self.frame_delay = 0.0
        if is_video:
            self.frame_delay = 1.0 / self.cap.get(cv2.CAP_PROP_FPS)

        print(f"frame_delay: {self.frame_delay}")
        self.q = queue.Queue()
        self.running = True
        self.thread = threading.Thread(target=self._reader)
        self.thread.start()

    def get(self, param):
        ''' Get properties of the video or stream being processed

        @param param    The property being requested

        @return The property being requested '''

        return self.cap.get(param)

    def release(self):
        ''' Release the cv2 video or stream being processed

        @param None

        @return The cv2 result of releasing the video or stream '''

        self.running = False
        self.thread.join()
        return self.cap.release()

    def read(self, timeout=0.05):
        ''' Retrieve the latest buffered frame

        @param timeout    If no frame is available after the timeout period, return None

        @return The latest buffered frame, or None if no frames are available '''

        try:
            return self.q.get(block=True, timeout=timeout)
        except queue.Empty:
            return None

    def _reader(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                print(f"Error: failed to read {self.input_path}")
                self.cap = cv2.VideoCapture(self.input_path)
                if not self.cap.isOpened():
                    print("Error: Unable to open RTSP stream")
                    break

            if not self.q.empty():
                try:
                    self.q.get_nowait()   # discard previous (unprocessed) frame
                except queue.Empty:
                    pass
            self.q.put(frame)

            if self.frame_delay:
                time.sleep(self.frame_delay)
