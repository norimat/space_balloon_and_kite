import pandas as pd
import re
import random

# テキストファイルのパス
file_path = ".\\analysis_bme280\\alrirude_1st.txt"
output_file = 'gps_data_1st.kml'

# 標高データを抽出する関数
def extract_altitude(line):
    match = re.search(r'Altitude:\s*([\d.]+)\s*m', line)
    if match:
        return float(match.group(1))
    return None

# テキストファイルをUTF-16エンコーディングで読み込み、標高データを抽出
with open(file_path, 'r', encoding='utf-16') as file:
    lines = file.readlines()
    altitudes = [extract_altitude(line) for line in lines if extract_altitude(line) is not None]

# DataFrameを作成
elevation_data = pd.DataFrame({
    'Elevation': altitudes
})

# 緯度経度のデータを追加
min_lat, min_lon = 35.145604, 139.612535  # 標高3mの緯度経度
max_lat, max_lon = 35.146928, 139.613372  # データ上の最高到達点の緯度経度

# 標高データの範囲を取得
min_elev, max_elev = elevation_data['Elevation'].min(), elevation_data['Elevation'].max()

# 緯度経度を線形補間で計算し、誤差を加える関数
def interpolate_with_error(value, min_value, max_value, min_lat, min_lon, max_lat, max_lon):
    lat = min_lat + (value - min_value) * (max_lat - min_lat) / (max_value - min_value)
    lon = min_lon + (value - min_value) * (max_lon - min_lon) / (max_value - min_value)
    
    # 1度の緯度は約111,000m
    # 1度の経度は約90,000m (緯度35度の場合)
    lat_error = random.uniform(-5, 5) / 111000
    lon_error = random.uniform(-5, 5) / 90000
    
    lat += lat_error
    lon += lon_error
    
    return lat, lon

# 緯度経度データを計算し、追加
latitude = []
longitude = []

for elevation in elevation_data['Elevation']:
    lat, lon = interpolate_with_error(elevation, min_elev, max_elev, min_lat, min_lon, max_lat, max_lon)
    latitude.append(lat)
    longitude.append(lon)

elevation_data['Latitude'] = latitude
elevation_data['Longitude'] = longitude

# KMLファイルの作成
def create_kml_tour(dataframe, output_file):
    kml_header = '''<?xml version="1.0" encoding="UTF-8"?>
    <kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2">
    <Document>
        <name>GPS Data Tour</name>
        <Style id="lineStyle">
            <LineStyle>
                <color>ff0000ff</color>
                <width>1</width>
            </LineStyle>
        </Style>
        <Placemark>
            <name>Path</name>
            <styleUrl>#lineStyle</styleUrl>
            <LineString>
                <tessellate>1</tessellate>
                <altitudeMode>relativeToGround</altitudeMode>
                <coordinates>'''
    
    kml_footer = '''
                </coordinates>
            </LineString>
        </Placemark>
        <gx:Tour>
            <name>GPS Tour</name>
            <gx:Playlist>'''
    
    kml_body = ''
    coordinates = ''
    num_points = len(dataframe)
    total_duration = 300  # ツアー全体の時間を300秒（5分）に設定
    duration_per_flyto = total_duration / (num_points - 1)  # 各ポイント間の飛行時間
    
    # 初期視点の設定
    previous_heading = random.uniform(0, 360)
    previous_tilt = random.uniform(70, 80)
    previous_range = random.uniform(250, 500)
    
    for index, row in dataframe.iterrows():
        coordinates += f'{row["Longitude"]},{row["Latitude"]},{row["Elevation"]} '
        
        # 視点の変更幅を設定
        heading = previous_heading + random.uniform(-5, 5)
        tilt = previous_tilt + random.uniform(-5, 5)
        range_val = previous_range + random.uniform(-50, 50)
        
        # rangeが1500mを超えないように調整
        range_val = min(range_val, 1500)
        
        # 視点の変更幅を適用
        previous_heading = heading
        previous_tilt = tilt
        previous_range = range_val
        
        if index < num_points - 1:
            kml_body += f'''
            <gx:FlyTo>
                <gx:duration>{duration_per_flyto}</gx:duration>
                <gx:flyToMode>smooth</gx:flyToMode>
                <LookAt>
                    <longitude>{row['Longitude']}</longitude>
                    <latitude>{row['Latitude']}</latitude>
                    <altitude>{row['Elevation']}</altitude>
                    <heading>{heading}</heading>
                    <tilt>{tilt}</tilt>
                    <range>{range_val}</range>
                    <gx:altitudeMode>relativeToGround</gx:altitudeMode>
                </LookAt>
            </gx:FlyTo>'''
    
    kml_content = kml_header + coordinates.strip() + kml_footer + kml_body + '''
        </gx:Playlist>
        </gx:Tour>
    </Document>
    </kml>'''
    
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(kml_content)

# KMLファイルを保存
create_kml_tour(elevation_data, output_file)

print(f"KML tour file has been created: {output_file}")
