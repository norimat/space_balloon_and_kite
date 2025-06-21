import time
import subprocess
import argparse

def get_voltage():
    """vcgencmd からコア電圧を取得する"""
    try:
        out = subprocess.check_output(['vcgencmd', 'measure_volts']).decode()
        return float(out.split('=')[1].replace('V', '').strip())
    except Exception as e:
        print(f"[Error] get_voltage(): {e}")
        return None

def get_throttled():
    """vcgencmd からスロットリング状態を取得する（16進数）"""
    try:
        out = subprocess.check_output(['vcgencmd', 'get_throttled']).decode()
        return out.strip().split('=')[1]
    except Exception as e:
        print(f"[Error] get_throttled(): {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Raspberry Pi Power Monitor Console Logger")
    parser.add_argument('--interval', type=float, default=1.0, help='出力間隔（秒）デフォルト: 1.0')
    args = parser.parse_args()

    start_time = time.time()
    print("elapsed_time (s) | voltage (V) | throttled status | timestamp")

    while True:
        try:
            now = time.time()
            elapsed = round(now - start_time, 6)
            voltage = get_voltage()
            throttled = get_throttled()
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

            print(f"{elapsed:>14.6f} | {voltage:>11.3f} | {throttled:>17} | {timestamp}")
            time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n[Info] Stopped by user.")
            break
        except Exception as e:
            print(f"[Error] main(): {e}")
            time.sleep(args.interval)

if __name__ == "__main__":
    main()
