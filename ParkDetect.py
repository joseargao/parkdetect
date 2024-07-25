#!/usr/bin/env python3
from datetime import datetime
import argparse

from modules.processors import YoloProcessor, read_zones_from_file, parse_media_format, MediaFormat
from modules.processors import StreamProcessor, ImageProcessor
from modules.protocol import Config, ZoneStatus, PwZoneState, SerialHandler


def percentage(val):
    ival = int(val)
    if ival < 0 or ival > 100:
        raise argparse.ArgumentTypeError(f"{val} is not a valid percentage value")
    return ival


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Park Detect',
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-i', '--input', type=str, help='Input file (image/video) or stream (rtsp)', default=None)
    parser.add_argument('-z', '--zones', type=str, required=True, help='Path to the zones config file')
    parser.add_argument('-m', '--model', type=str, help='Model file used for object detection', default="yolov8n.pt")
    parser.add_argument('-c', '--canvas', action="store_true", help='Display the canvas', default=False)
    parser.add_argument('-o', '--output', type=str, help='Path to the result file', default=None)
    parser.add_argument('-s', '--size', type=int, help='The image size paramter for the model', default=640)
    parser.add_argument('-t', '--track', action="store_true", help='Track objects', default=False)
    parser.add_argument('-p', '--percentage', type=percentage, help='Percentage certainty to detect vehicles',
                        default=25)
    parser.add_argument('-g', '--graphics', type=str, help='Mask to enable/disable graphics i.e. "zodl"',
                        default="zodl")
    parser.add_argument('-b', '--bytebeam', action="store_true", help='Create a ByteBeam endpoint', default=False)
    parser.add_argument('-a', '--allow', type=str, help='Comma separated list of detect types to allow', default=None)
    parser.add_argument('-d', '--detect_zones', type=str, help='Model file used for zone detection', default="zone.pt")
    parser.add_argument('-l', '--license_plate', type=str, help='Model file used for license plate detection', default="licenseplate.pt")  # noqa
    parser.add_argument('-r', '--auto_record', type=int, help='the duration to wait before auto_record is invoked')

    args = parser.parse_args()

    begin = datetime.now()
    config = Config(confidence_threshold=args.percentage, tracking=args.track)
    model = YoloProcessor(args.model, args.size, config.tracking, config.confidence_threshold, args.allow)
    zone_model = YoloProcessor(args.detect_zones, args.size, config.tracking, config.confidence_threshold, args.allow)
    plate_model = YoloProcessor(args.license_plate, args.size, config.tracking, config.confidence_threshold, args.allow)
    print(f"Models loaded: {(datetime.now() - begin).total_seconds():.3f}")

    input_path = args.input
    input_format = parse_media_format(input_path)

    zones_cfg = args.zones
    zones = read_zones_from_file(zones_cfg)

    processor = None
    pygame_module = None
    enable_canvas = args.canvas or args.output
    if enable_canvas:
        import pygame as pygame
        pygame_module = pygame

    serial_handler = None
    if args.bytebeam:
        serial_handler = SerialHandler(zones=zones, config=config)
        serial_handler.start_rx_thread()

    if input_format is MediaFormat.IMAGE:
        processor = ImageProcessor(input_path, model, zone_model, plate_model, zones, zones_cfg,
                                   enable_canvas, args.output, args.graphics, serial_handler)
    elif input_format in [MediaFormat.VIDEO, MediaFormat.STREAM]:
        processor = StreamProcessor(input_path, input_format, model, zone_model, plate_model, zones, zones_cfg,
                                    enable_canvas, args.output, args.graphics, serial_handler, args.auto_record)

    try:
        running = True
        while running:
            if pygame_module:
                for event in pygame_module.event.get():
                    if event.type == pygame_module.QUIT:
                        running = False
                    else:
                        processor.handle_event(event)

            processor.render()

    except KeyboardInterrupt:
        print("KeyboardInterrupt")

    finally:
        processor.finalize()
        if args.bytebeam:
            serial_handler.stop_rx_thread()
