# 🔋 Raspberry Pi Power Monitor

Raspberry Pi 上で動作する、**電圧・スロットリング状態・時刻**をリアルタイムでコンソールに表示する軽量モニタリングツールです。

## 🚀 特徴

- 1秒ごと（または任意の間隔）で以下の情報を出力：
  - コア電圧（`vcgencmd measure_volts`）
  - スロットリング状態（`vcgencmd get_throttled`）
  - 測定開始からの経過時間
  - 現在時刻
- ファイル保存なし、**コンソール出力のみ**
- 追加ライブラリ不要（標準ライブラリのみ）
- 出力間隔はコマンドラインで自由に指定可能

---

## 🧰 動作環境

- Raspberry Pi（`vcgencmd` コマンドが有効であること）
- Python 3.x

---

## ⚙️ 使い方

python3 power_monitor.py [--interval 秒数]

## オプション
オプション名	説明	デフォルト

--interval	出力間隔（秒単位）	1.0 秒

## 💡 実行例
- 1秒ごとに出力する場合：

    python3 power_monitor.py

- 0.5秒ごとに出力する場合：

    python3 power_monitor.py --interval 0.5

## 📤 出力例
    elapsed_time (s) | voltage (V) | throttled status | timestamp
      0.000000   |      0.861  |           0x0    | 2025-06-15 16:30:01
      1.001234   |      0.860  |         0x50000  | 2025-06-15 16:30:02
      2.002345   |      0.859  |         0x50000  | 2025-06-15 16:30:03


## 🧠 throttled（スロットリング）状態の解釈
vcgencmd get_throttled の出力は16進数のビットフラグで、電力や熱の状態を示します。代表的な値は以下の通りです：

値	意味
0x0	問題なし（正常）
0x1	現在 電圧が不足している（アンダーボルト）
0x2	現在 周波数が制限されている
0x50000	過去に アンダーボルトまたは周波数制限が発生

詳細なビットの意味は Raspberry Pi Documentation を参照してください。

## 🛑 停止方法
Ctrl + C を押して停止します。