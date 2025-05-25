import time
import smbus2
import bme280
import math

# --- 標準定数 ---
P0 = 1013.25  # 海面気圧 [hPa]
L = 0.0065    # 対流圏の気温減率 [K/m]
T0 = 288.15   # 海面付近の標準気温 [K]
g = 9.80665   # 重力加速度 [m/s^2]
R = 287.05    # 空気の気体定数 [J/(kg·K)]

# --- I2C設定 ---
port = 1
address = 0x76  # または 0x77 の可能性あり
bus = smbus2.SMBus(port)

# BMP280 の初期化
calibration_params = bme280.load_calibration_params(bus, address)

def read_bmp280():
    data = bme280.sample(bus, address, calibration_params)
    temperature = data.temperature  # [°C]
    pressure = data.pressure        # [hPa]
    return temperature, pressure

def calculate_altitude(temp_c, pressure_hpa):
    """湿度補正なし・BMP280専用の高度計算"""
    T = temp_c + 273.15  # K に変換

    if pressure_hpa > 226.32:  # 高度 < 11 km（対流圏）
        altitude = (T0 / L) * (1 - (pressure_hpa / P0) ** (R * L / g))
    else:  # 高度 >= 11 km（成層圏）
        h0 = 11000      # m
        T1 = 216.65     # K（成層圏の標準気温）
        P1 = 226.32     # hPa（高度11km時の気圧）
        altitude = h0 + (-R * T1 / g) * math.log(pressure_hpa / P1)

    return altitude

if __name__ == "__main__":
    try:
        while True:
            temp, pressure = read_bmp280()
            altitude = calculate_altitude(temp, pressure)

            print(f"\n温度     : {temp:.2f} °C")
            print(f"気圧     : {pressure:.2f} hPa")
            print(f"算出高度 : {altitude:.2f} m")

            time.sleep(1)

    except KeyboardInterrupt:
        print("終了しました")
