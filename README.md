This is a demo program that uses Ultralytics YOLOv8 for detection of vehicles, parking spaces and license plates. If you have a video file with a parking lot, you can test it as below:

./ParkDetect.py -z ./zones.cfg -i ../parking.mp4 -c -m yolov8n.pt -d zone.pt -a 2,7

Use the command line help to understand the available options.
