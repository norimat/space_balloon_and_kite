from picamera2 import Picamera2
import time

frame_interval = 1.0 / 30  # 30fps
output_file    = open("output_yuv420_mov.yuv", "wb")
picam2         = Picamera2()
video_config   = picam2.create_video_configuration(main={"format": "YUV420", "size": (1920, 1080)})
picam2.configure(video_config)

picam2.start()
time.sleep(1)

frame_count = 0
start_time  = time.time()
duration    = 5 # record 5sec

while time.time() - start_time < duration:
    frame_start = time.time()
    yuv_frame   = picam2.capture_array("main")

    output_file.write(yuv_frame.tobytes())

    frame_count += 1

    elapsed    = time.time() - frame_start
    sleep_time = max(0, frame_interval - elapsed)
    time.sleep(sleep_time)

output_file.close()
picam2.stop()
print(f"{frame_count} frames saved at ~30fps.")
print("If you want to convert to MP4, please execute the following command.")
print("->  ffmpeg -f rawvideo -pixel_format yuv420p -video_size 1920x1080 -framerate 30 -i output_yuv420_mov.yuv -c:v libx264 -preset fast -crf 23 output_yuv420_conv.mp4")
