import time
import smbus2
import bme280
import numpy as np
import math

# --- 標準定数 ---
P0 = 1013.25  # 海面気圧 [hPa]
L = 0.0065    # 対流圏の気温減率 [K/m]
T0 = 288.15   # 海面付近の標準気温 [K]
g = 9.80665   # 重力加速度 [m/s^2]
R = 287.05    # 空気の気体定数 [J/(kg·K)]

# --- I2C設定 ---
port = 1
address = 0x76  # or 0x77 depending on your wiring
bus = smbus2.SMBus(port)

# --- BME/BMP280の初期化 ---
calibration_params = bme280.load_calibration_params(bus, address)

def read_sensor():
    data = bme280.sample(bus, address, calibration_params)
    temperature = data.temperature  # [°C]
    pressure = data.pressure        # [hPa]
    humidity = getattr(data, 'humidity', None)  # BME280なら値がある、BMP280ならNone
    return temperature, pressure, humidity

def saturation_vapor_pressure(temp_c):
    """飽和水蒸気圧の計算（hPa）"""
    return 6.112 * math.exp((17.67 * temp_c) / (temp_c + 243.5))

def mixing_ratio(e, p):
    """混合比 r の計算"""
    return 0.622 * e / (p - e)

def virtual_temperature(temp_c, humidity, pressure):
    """仮想温度の計算（湿度を考慮した空気の温度）"""
    T = temp_c + 273.15  # [K]
    e = humidity / 100.0 * saturation_vapor_pressure(temp_c)  # 実際の水蒸気圧
    r = mixing_ratio(e, pressure)
    Tv = T * (1 + 0.61 * r)
    return Tv

def calculate_altitude(temp_c, pressure_hpa, humidity=None):
    """高度の計算（湿度がある場合は仮想温度使用）"""
    if humidity is not None:
        T = virtual_temperature(temp_c, humidity, pressure_hpa)
    else:
        T = temp_c + 273.15

    if pressure_hpa > 226.32:  # 対流圏 (高度 < 11 km)
        altitude = (T0 / L) * (1 - (pressure_hpa / P0) ** (R * L / g))
    else:  # 成層圏（温度一定）
        h0 = 11000  # m
        T1 = 216.65  # K
        P1 = 226.32  # hPa
        altitude = h0 + (-R * T1 / g) * math.log(pressure_hpa / P1)

    return altitude

if __name__ == "__main__":
    try:
        while True:
            temp, pressure, humidity = read_sensor()
            altitude = calculate_altitude(temp, pressure, humidity)

            print(f"\n温度     : {temp:.2f} °C")
            print(f"気圧     : {pressure:.2f} hPa")
            if humidity is not None:
                print(f"湿度     : {humidity:.2f} %")
            else:
                print("湿度     : 測定不可 (BMP280)")
            print(f"算出高度 : {altitude:.2f} m")

            time.sleep(1)

    except KeyboardInterrupt:
        print("終了しました")
