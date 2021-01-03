#!/usr/bin/python -u
# -*- coding: utf-8 -*-

import sys
from docopt import docopt

################################################
# 更新情報
################################################

f_ver = "get_data_2020_12_31"
# 新規作成

################################################
# オプション設定
################################################
# オプションのヘルプドキュメントをdocstringを使って記載
__doc__ = """{f}

Usage:
    {f} [-b|--brmtrc <BAROMETRIC-DATA_FILE>] [-g|--gps <GPS-DATA_FILE>] [-o|--output <KML_FILE>] [-l|--leveloffset <hight[m]>]
    {f} -v|--version
    {f} -h|--help

Options:
    -o --output <KML_FILE>              出力ファイル名を指定。GoogleEarthにimport可能なKMLフォーマットで出力します。デフォルトは"result.kml"です。
    -b --brmtrc <BAROMETRIC-DATA_FILE>  BME280で取得した気圧,気温,湿度の各データのファイル名を指定します。必須オプションです。
    -g --gps <GPS-DATA_FILE>            小型高感度GPSモジュールGYSFDMAXBで取得したGPXフォーマットのファイル名を指定します。必須オプションです。
    -l --leveloffset <hight[m]>         フライト位置の海抜を[m]で指定します。指定しない場合は1013.25hPaを海抜0mとして計算します。
    -v --version                        show Version of {f} and exit.
    -h --help                           show Help docment data this screen and exit.
""".format(f=__file__)

# オプションパーサー
def parse():
    args = docopt(__doc__)
    fileset = []
    if args['--version']:
        sline = " Version is " + str(f_ver) + "."
        print(sline)
        sys.exit()

    if args['--brmtrc']:
        ifname = args['--brmtrc'][0]
        sline = " Input BAROMETRIC-DATA File Name = " + ifname
        print(sline)
        fileset.append(ifname)
    else:
        sline = " Input BAROMETRIC-DATA File is Empty !!!"
        print(sline)
        sys.exit()

    if args['--gps']:
        ifname = args['--gps'][0]
        sline = " Input GPS-DATA File Name = " + ifname
        print(sline)
        fileset.append(ifname)
    else:
        sline = " Input GPS-DATA File is Empty !!!"
        print(sline)
        sys.exit()

    if args['--output']:
        ofname = args['--output'][0]
        sline = " Output File Name = " + ofname
        print(sline)
        fileset.append(ofname)
    else:
        args['--output'].append("result.kml")
        ofname = args['--output'][0]
        sline = " Output File Name = " + ofname
        print(sline)
        fileset.append(ofname)

    if args['--leveloffset']:
        offset = args['--leveloffset'][0]
        sline = " Setted Level Offset = " + offset
        print(sline)

    return fileset

# オプションパーサーのValueを確認(Debug用)
def check_parse():
    print("  {0:<20}{1:<20}{2:<20}".format("kye", "value", "type"))
    print("  {0:-<60}".format(""))
    for k,v in args.items():
        print("  {0:<20}{1:<20}{2:<20}".format(str(k), str(v), str(type(v))))

################################################
# BME280で取得したデータから標高を計算するクラス
################################################
class analysis_bme280:
    def __init__(self, ifname):
        self.ifname = ifname

    # 標高データへ変換する関数
    def get_AboveSeaLevel(self):
        # データファイルから各データの読み込み
        plist = []
        tlist = []
        hlist = []
        cnt = 0
        i = 0
        for line in open(str(self.ifname), 'r'):
            datas = line.split()
            plist.append(datas[2])
            tlist.append(datas[6])
            cnt += 1

        if args['--leveloffset']:
            # 最大気圧を海面上の気圧として抽出
            p0 = float(max(plist))
            # 海抜のオフセットを指定
            hoffset = float(args['--leveloffset'][0])
        else:
            # 海面上の気圧を1013.25として設定
            p0 = 1013.25
            # 海抜のオフセットに0mを指定
            hoffset = 0

        # 気温・気圧のデータから標高を計算
        for i in range(cnt):
            p = float(plist[i])
            t = float(tlist[i])
            h = ((((p0 / p) ** (1 / 5.257) - 1) * (t + 273.15)) / 0.0065 + hoffset)
            hlist.append(h)
            # print ( " i = " + str(i) + ", p = " + str(p) + ", t = " + str(t) + ", h = " + str(h) )

        return hlist

################################################
# 小型高感度GPSモジュールGYSFDMAXBで取得したGPXデータから緯度・経度を抽出するクラス
################################################
class survey_gpx:
    def __init__(self, ifname):
        self.ifname = ifname

    # GPXファイルから緯度・経度を抽出する関数
    def get_GPSdata(self):
        cnt = 0
        gpslist = []
        for line in open(str(self.ifname), 'r'):
            datas = line.split()
            if str(datas[0]) == "<trkpt":
                lat = datas[1].split("=")
                lat = lat[1].strip("\"")
                lat = lat.strip(">")
                lon = datas[2].split("=")
                lon = lon[1].strip("\"")
                lon = lon.strip("\">")
                # print ( " cnt = " + str(cnt) + ", lat = " + str(lat) + ", lon = " + str(lon) )
                cnt += 1
                gpslist.append([lat,lon])

        # データファイルから各データの読み込み
        return gpslist

################################################
# 計算した標高リストと抽出した緯度経度リストからKMLフォーマットファイルを作成
################################################
class gen_kml:
    def __init__(self, hlist, gpslist, ofname):
        self.hlist   = hlist
        self.gpslist = gpslist
        self.ofname  = ofname

    # KMLフォーマットファイルを作成する関数
    def mk_file(self):

        # 標高リストと緯度経度リストのうち要素数が少ないほうをデータ数とする
        hlen = len(self.hlist)
        gpslen = len(self.gpslist)
        if hlen < gpslen:
            setlen = hlen
        else:
            setlen = gpslen

        # KMLフォーマットとして出力するファイルをオープン
        f = open(str(self.ofname), 'w')

        # ヘッダを出力
        f.write("<?xml version=\"1.0\" encoding=\"utf-8\" standalone=\"yes\"?>\n")
        f.write("<kml xmlns=\"http://www.opengis.net/kml/2.2\">\n")
        f.write("  <Document>\n")
        f.write("    <name><![CDATA[gpslog]]></name>\n")
        f.write("    <visibility>1</visibility>\n")
        f.write("    <open>1</open>\n")
        f.write("    <Folder id=\"SpaceBalloon\">\n")
        f.write("      <name>SpaceBalloon</name>\n")
        f.write("      <visibility>1</visibility>\n")
        f.write("      <open>0</open>\n")
        f.write("      <Placemark>\n")
        f.write("        <name><![CDATA[gpslog]]></name>\n")
        f.write("        <Snippet></Snippet>\n")
        f.write("        <description><![CDATA[&nbsp;]]></description>\n")
        f.write("        <Style>\n")
        f.write("          <LineStyle>\n")
        f.write("            <color>ff0000e6</color>\n")
        f.write("            <width>4</width>\n")
        f.write("          </LineStyle>\n")
        f.write("        </Style>\n")
        f.write("        <LineString>\n")
        f.write("          <tessellate>1</tessellate>\n")
        f.write("          <altitudeMode>absolute</altitudeMode>\n")
        f.write("          <coordinates>\n")

        # 気温・気圧のデータから標高を計算
        for i in range(setlen):
            h = self.hlist[i]
            gps = self.gpslist[i]
            lat = gps[0]
            lon = gps[1]
            f.write("            " + str(lon) + "," + str(lat) + "," + str(h) + " \n")

        # フッタを出力
        f.write("          </coordinates>\n")
        f.write("        </LineString>\n")
        f.write("      </Placemark>\n")
        f.write("    </Folder>\n")
        f.write("  </Document>\n")
        f.write("</kml>\n")

        f.close()

################################################
# main
################################################
if __name__ == '__main__':
    args = docopt(__doc__)
    # check_parse()
    fileset = parse()
    dataline = analysis_bme280(fileset[0])
    hdataline = dataline.get_AboveSeaLevel()
    dataline = survey_gpx(fileset[1])
    gpsdataline = dataline.get_GPSdata()
    dataline = gen_kml(hdataline, gpsdataline, fileset[2])
    dataline.mk_file()


