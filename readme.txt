space_balloon_and_kite:.
|
│  readme.txt               ：本ファイル
│
├─c                         ：cソースコードの格納ディレクトリ
├─log                       ：測定結果の格納ディレクトリ
│  └─data_yyyymmddhhmmss    ：yyyymmddhhmmssに測定を開始したデータの格納ディレクトリ
│      │  bme280.log        ：BME-280で測定した気温,湿度,気圧のデータ出力結果
│      │  gpslog.gpx        ：GYSFDMAXBで受信したGPS受信データ出力結果
│      │  mpu6050.log       ：MPU-6050で測定した各速度,角速度,気温のデータ出力結果
│      │  mpu9250.log       ：MPU-9250で測定した加速度,角速度,磁場,気温のデータ出力結果
│      │
│      └─pictures           ：Raspberry Pi Zero用スパイカメラでタイムラプス撮影した画像データの出力先
│
├─python                    ：pythonスクリプトの格納ディレクトリ
│  │  run_bme280.py         ：BME-280の測定用スクリプト
│  │  run_mpu6050.py        ：MPU-6050の測定用スクリプト
│  │  run_mpu9250.py        ：MPU-9250の測定用スクリプト
│  │
│  ├─analysis               ：ポスト解析用スクリプトの格納ディレクトリ
│  │      get_data.py       ：gpslog.gpxをGoogleEarthに取り込むKMLフォーマットへ変換するスクリプト
│  │      result.kml        ：gpslog.gpxをKMLフォーマットへ変換した結果
│  │
│  ├─driver                 ：センサーのドライバスクリプトの格納ディレクトリ
│  └─test                   ：テスト用スクリプトの格納先ディレクトリ
│          test0_L80_M39.py ：L80_M39で受信したGPS受信データ出力スクリプト(受信せず)
│          test1_L80_M39.py ：L80_M39で受信したGPS受信データ出力スクリプト(受信せず)
│          test2_L80_M39.py ：L80_M39で受信したGPS受信データ出力スクリプト(受信せず)
│
└─sh                        ：シェルスクリプトの格納ディレクトリ
　      get_still.sh         ：Raspberry Pi Zero用スパイカメラでの撮影実行スクリプト
　      go.sh                ：RaspberryPiZero起動直後にデータ格納ディレクトリ作成と各種測定用スクリプトを実行するスクリプト
　      run_gpxlogger.sh     ：GPS受信を開始するスクリプト
　      timelapse.sh         ：get_still.shを使ったタイムラプス撮影を実行するスクリプト

