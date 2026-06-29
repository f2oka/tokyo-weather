# 東京 気温・天気くらべダッシュボード

東京の日別気象データ（最高・最低・平均気温、天気）を **Open-Meteo** から毎日自動収集し、
**昨年の同じ日**と比較表示するダッシュボードです。GitHub Actions で完全自動更新されます。

## 構成

```
weather-dashboard/
├─ index.html                  ダッシュボード本体（ブラウザで開くだけで動く）
├─ data/weather.json           収集済みデータ（自動更新される）
├─ scripts/collect.py          Open-Meteo から収集するスクリプト
└─ .github/workflows/daily.yml 毎日6:00(JST)に収集→コミット→Pages公開
```

## データソース

[Open-Meteo](https://open-meteo.com/) — APIキー不要・無料（非商用、1日1万コールまで）。
データは CC BY 4.0。本ダッシュボードは出典を画面下部に明記しています。

- 今年（直近）: Forecast API の `past_days`
- 昨年同期間: Historical Forecast API（実測に近い再解析・予報アーカイブ）
- 地点: 東京（緯度 35.6895 / 経度 139.6917）

## 動かし方

### すぐ見る
`index.html` をブラウザで開くだけ。ページは起動時にブラウザから直接 Open-Meteo を叩いて
最新データを取得します（「ライブ取得」表示）。取得に失敗した場合は同梱の `data/weather.json`
を表示します（「保存データ表示」）。

### 毎日自動更新（GitHub Pages）
1. このフォルダを GitHub リポジトリにプッシュ
2. リポジトリの Settings → Pages → Source を **GitHub Actions** に設定
3. Settings → Actions → General → Workflow permissions を **Read and write** に
4. 以降、毎日 JST 6:00 に `collect.py` が走り、`data/weather.json` を更新してコミットし、
   Pages に再デプロイします。手動実行は Actions タブの「Run workflow」から。

### 手元で収集だけ試す
```bash
python3 scripts/collect.py
```
`data/weather.json` に直近35日分＋昨年同期間が蓄積されます（日付キーで重複排除）。

## 見方

- **サマリーカード**: 最新日の天気、最高気温の昨年差、直近30日の平均気温・雨日数の昨年比
- **気温の地層**: 各日に2本の帯。左（斜線）が昨年同日、右が今年。
  帯の高さ＝その日の最高〜最低の幅、色＝暖かさ（寒色→暖色）、絵文字＝天気。
  バーにふれると詳細（昨年との最高気温差・降水量）が出ます。

## カスタマイズ

- 表示日数: `index.html` 内 `buildPairs` の `slice(-30)` を変更
- 収集期間: `scripts/collect.py` の `LOOKBACK_DAYS`
- 別の都市: `LATITUDE` / `LONGITUDE`（collect.py と index.html の両方）
- 更新時刻: `.github/workflows/daily.yml` の cron（UTC指定）
```
