ast Update 2024.8.23

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
│  │  run_bme280.py         ：BME-280の測定用スクリプト         参照先https://qiita.com/_saki_kawa_/items/7961c82b150a01920d72
│  │  run_mpu6050.py        ：MPU-6050の測定用スクリプト        参照先http://manabi.science/library/2017/02121501/
│  │  run_mpu9250.py        ：MPU-9250の測定用スクリプト        参照先https://modalsoul.hatenablog.com/entry/2018/10/07/222242
│  │                                                          　※↑利用するFaBo9Axis_MPU9250ライブラリのFaBo9Axis_MPU9250/MPU9250.pyファイル内のprint文をすべてpython3ように()閉じに修正が必要
│  │
│  ├─analysis               ：ポスト解析用スクリプトの格納ディレクトリ
│  │      get_data.py       ：gpslog.gpxをGoogleEarthに取り込むKMLフォーマットへ変換するスクリプト
│  │      result.kml        ：gpslog.gpxをKMLフォーマットへ変換した結果
│  │
│  ├─driver                 ：センサーのドライバスクリプトの格納ディレクトリ
│  └─test                   ：テスト用スクリプトの格納先ディレクトリ
│          test0_L80_M39.py ：L80_M39で受信したGPS受信データ出力スクリプト(受信せず)    参照先https://wiki.52pi.com/index.php/USB-Port-GPS_Module_SKU:EZ-0048
│          test1_L80_M39.py ：L80_M39で受信したGPS受信データ出力スクリプト(受信せず)    参照先https://wiki.52pi.com/index.php/USB-Port-GPS_Module_SKU:EZ-0048
│          test2_L80_M39.py ：L80_M39で受信したGPS受信データ出力スクリプト(受信せず)    参照先https://wiki.52pi.com/index.php/USB-Port-GPS_Module_SKU:EZ-0048
│          run_mpu9250.py   ：MPU-9250の測定用スクリプト(動作せず)                     参照先https://qiita.com/boyaki_machine/items/915f7730c737f2a5cc79
│
└─sh                        ：シェルスクリプトの格納ディレクトリ
        exe_script.sh        : Cronで自動起動しないpythonコマンドへの対応                                               参照先https://qiita.com/Yokohide/items/b4ddc81372501668aa9c
　      get_still.sh         ：Raspberry Pi Zero用スパイカメラでの撮影実行スクリプト                                   　参照先https://qiita.com/ikemura23/items/4f949d47489e6c5ff6a2
　      go.sh                ：RaspberryPiZero起動直後にデータ格納ディレクトリ作成と各種測定用スクリプトを実行するスクリプト
　      run_gpxlogger.sh     ：GPS受信を開始するスクリプト                                                              参照先https://denor.jp/raspberry-pi%E3%81%AB%E3%80%8C%E3%81%BF%E3%81%A1%E3%81%B3%E3%81%8D%E3%80%8D%E5%AF%BE%E5%BF%9Cgps%E3%83%A2%E3%82%B8%E3%83%A5%E3%83%BC%E3%83%AB%E3%82%92%E6%8E%A5%E7%B6%9A
　      timelapse.sh         ：get_still.shを使ったタイムラプス撮影を実行するスクリプト                                   参照先https://shima-nigoro.hatenablog.jp/entry/2016/07/24/235846

