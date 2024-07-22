import math

# 定数
R = 287.05  # J/(kg*K) 気体定数
g = 9.80665  # m/s^2 重力加速度

def calculate_altitude(pressure, temp, sea_level_pressure, sea_level_altitude):
    temp_k = temp + 273.15  # 摂氏からケルビンへ変換
    altitude = sea_level_altitude + (R * temp_k / g) * math.log(sea_level_pressure / pressure)
    return altitude

# テキストファイルの読み込みと標高計算
def process_file(file_path):
    results = []
    sea_level_altitude = 3  # 海抜3m
    sea_level_pressure = None

    with open(file_path, 'r') as file:
        for line in file:
            parts = line.split(',')
            pressure = float(parts[0].split(':')[1].strip().split()[0])
            temp = float(parts[1].split(':')[1].strip().split()[0])

            if sea_level_pressure is None:
                sea_level_pressure = pressure

            altitude = calculate_altitude(pressure, temp, sea_level_pressure, sea_level_altitude)
            results.append((pressure, temp, altitude))

    return results

# 使用例
file_path = '..\\..\\..\\log\\data_20240720135313\\bme280.log'
results = process_file(file_path)

for pressure, temp, altitude in results:
    print(f"Pressure: {pressure:.5f} hPa, Temp: {temp:.5f} °C, Altitude: {altitude:.2f} m")


