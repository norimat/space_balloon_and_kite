from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
import time
import threading
import signal
import sys

running     = True
frame_count = 0
frame_ready = threading.Event()

def signal_handler(sig, frame):
    global running
    print("\nCtrl+C detected. Stopping recording...")
    running = False

signal.signal(signal.SIGINT, signal_handler)

def on_frame(request):
    global frame_count
    frame_count += 1
    frame_ready.set()

picam2  = Picamera2()
encoder = H264Encoder(bitrate=8000000)
config = picam2.create_video_configuration(
    main={"format": "YUV420", "size": (1920, 1080)},
    controls={"FrameDurationLimits": (33333, 33333)}  # 30fps = 1/30s = 33333μs
)
picam2.configure(config)
picam2.post_callback = on_frame

picam2.start()
picam2.start_encoder(encoder, output="output_h264encoder.h264")

print("Recording... Press Ctrl+C to stop.")

try:
    start_unix_epoc = time.time()
    while running:
        if frame_ready.wait(timeout=1.0):
            frame_ready.clear()            
            print(f"VSYNC Frame {frame_count} captured. " + str(time.time() - start_unix_epoc) )
        else:
            print("Waiting for frame...")
finally:
    picam2.stop_encoder()
    picam2.stop()
    print(f"Recording stopped. Total frames: {frame_count}")
    print("If you want to convert to MP4, please execute the following command.")
    print("ffmpeg -framerate 30 -i output_h264encoder.h264 -c copy output_h264encoder.mp4")
