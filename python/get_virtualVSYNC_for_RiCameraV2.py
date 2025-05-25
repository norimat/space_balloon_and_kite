from picamera2 import Picamera2
import time

# カメラ初期化
picam2 = Picamera2()
config = picam2.create_video_configuration(main={"size": (640, 480)})
picam2.configure(config)
picam2.start()

print("フレーム取得開始（Ctrl+Cで停止）")

try:
    while True:
        # フレームを取得（メタデータ付き）
        frame = picam2.capture_array("main")
        metadata = picam2.capture_metadata()

        # SensorTimestamp（ナノ秒単位）を取得
        sensor_timestamp_ns = metadata.get("SensorTimestamp")
        if sensor_timestamp_ns:
            timestamp_sec = sensor_timestamp_ns / 1e9
            print(f"SensorTimestamp: {sensor_timestamp_ns} ns ({timestamp_sec:.6f} s)")
        else:
            print("タイムスタンプ情報が取得できませんでした。")

        # 表示間隔調整（任意）
        time.sleep(1/30)  # 30 FPS想定
except KeyboardInterrupt:
    print("停止しました。")

picam2.stop()
