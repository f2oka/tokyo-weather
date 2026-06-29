#!/usr/bin/env python3
"""
東京の日別気象データを Open-Meteo から収集し、data/weather.json に蓄積する。
- 今年分: Forecast API の past_days で直近を取得（実測に近い Historical Forecast 系）
- 昨年分: Historical Forecast API で同じ日付の1年前を取得
毎日 GitHub Actions から実行される想定。日付をキーに重複排除する。

データ出典: Open-Meteo (https://open-meteo.com/) / CC BY 4.0
"""

import json
import sys
import urllib.request
import urllib.parse
from datetime import date, timedelta
from pathlib import Path

# 東京（気象庁東京地点に近い座標）
LATITUDE = 35.6895
LONGITUDE = 139.6917
TIMEZONE = "Asia/Tokyo"

DAILY_VARS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "weather_code",
    "precipitation_sum",
]

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "weather.json"

# 直近何日分を毎回取り直すか（観測値の事後修正に追従するため少し広めに取る）
LOOKBACK_DAYS = 35

FORECAST_BASE = "https://api.open-meteo.com/v1/forecast"
HISTORICAL_BASE = "https://historical-forecast-api.open-meteo.com/v1/forecast"


def fetch(base_url: str, params: dict) -> dict:
    url = base_url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "tokyo-weather-dashboard"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def to_records(payload: dict) -> dict:
    """Open-Meteo の daily ブロックを {date: {...}} 形式に変換"""
    daily = payload.get("daily", {})
    times = daily.get("time", [])
    out = {}
    for i, d in enumerate(times):
        out[d] = {
            "date": d,
            "t_max": daily.get("temperature_2m_max", [None] * len(times))[i],
            "t_min": daily.get("temperature_2m_min", [None] * len(times))[i],
            "t_mean": daily.get("temperature_2m_mean", [None] * len(times))[i],
            "weather_code": daily.get("weather_code", [None] * len(times))[i],
            "precip": daily.get("precipitation_sum", [None] * len(times))[i],
        }
    return out


def collect_recent() -> dict:
    """今年（直近）分を取得"""
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "daily": ",".join(DAILY_VARS),
        "timezone": TIMEZONE,
        "past_days": LOOKBACK_DAYS,
        "forecast_days": 1,
    }
    return to_records(fetch(FORECAST_BASE, params))


def collect_last_year() -> dict:
    """昨年の同期間分を Historical Forecast API から取得"""
    today = date.today()
    end = today - timedelta(days=365)
    start = end - timedelta(days=LOOKBACK_DAYS)
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "daily": ",".join(DAILY_VARS),
        "timezone": TIMEZONE,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
    }
    return to_records(fetch(HISTORICAL_BASE, params))


def load_store() -> dict:
    if DATA_PATH.exists():
        try:
            return json.loads(DATA_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def main() -> int:
    store = load_store()

    try:
        recent = collect_recent()
        last_year = collect_last_year()
    except Exception as e:  # noqa: BLE001
        print(f"取得に失敗しました: {e}", file=sys.stderr)
        return 1

    # 日付キーでマージ（新しい取得値で上書き = 事後修正に追従）
    merged = {**store, **recent, **last_year}

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    ordered = dict(sorted(merged.items()))
    DATA_PATH.write_text(
        json.dumps(ordered, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    print(f"保存しました: {len(ordered)} 日分 -> {DATA_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
