import json
import os
import time
import urllib.request
from datetime import datetime, timedelta, timezone

# 47都道府県庁所在地のリスト
CITIES = [
    {"id": "sapporo", "name": "札幌市", "lat": 43.0642, "lon": 141.3469},
    {"id": "aomori", "name": "青森市", "lat": 40.8244, "lon": 140.7400},
    {"id": "morioka", "name": "盛岡市", "lat": 39.7036, "lon": 141.1527},
    {"id": "sendai", "name": "仙台市", "lat": 38.2688, "lon": 140.8721},
    {"id": "akita", "name": "秋田市", "lat": 39.7186, "lon": 140.1024},
    {"id": "yamagata", "name": "山形市", "lat": 38.2404, "lon": 140.3636},
    {"id": "fukushima", "name": "福島市", "lat": 37.7503, "lon": 140.4676},
    {"id": "mito", "name": "水戸市", "lat": 36.3418, "lon": 140.4468},
    {"id": "utsunomiya", "name": "宇都宮市", "lat": 36.5551, "lon": 139.8828},
    {"id": "maebashi", "name": "前橋市", "lat": 36.3911, "lon": 139.0608},
    {"id": "saitama", "name": "さいたま市", "lat": 35.8569, "lon": 139.6489},
    {"id": "chiba", "name": "千葉市", "lat": 35.6074, "lon": 140.1065},
    {"id": "tokyo", "name": "東京都", "lat": 35.6895, "lon": 139.6917},
    {"id": "yokohama", "name": "横浜市", "lat": 35.4478, "lon": 139.6425},
    {"id": "niigata", "name": "新潟市", "lat": 37.9026, "lon": 139.0236},
    {"id": "toyama", "name": "富山市", "lat": 36.6953, "lon": 137.2113},
    {"id": "kanazawa", "name": "金沢市", "lat": 36.5947, "lon": 136.6256},
    {"id": "fukui", "name": "福井市", "lat": 36.0652, "lon": 136.2219},
    {"id": "kofu", "name": "甲府市", "lat": 35.6642, "lon": 138.5684},
    {"id": "nagano", "name": "長野市", "lat": 36.6513, "lon": 138.1812},
    {"id": "gifu", "name": "岐阜市", "lat": 35.4233, "lon": 136.7607},
    {"id": "shizuoka", "name": "静岡市", "lat": 34.9769, "lon": 138.3831},
    {"id": "nagoya", "name": "名古屋市", "lat": 35.1815, "lon": 136.9066},
    {"id": "tsu", "name": "津市", "lat": 34.7303, "lon": 136.5086},
    {"id": "otsu", "name": "大津市", "lat": 35.0045, "lon": 135.8686},
    {"id": "kyoto", "name": "京都市", "lat": 35.0116, "lon": 135.7681},
    {"id": "osaka", "name": "大阪市", "lat": 34.6937, "lon": 135.5022},
    {"id": "kobe", "name": "神戸市", "lat": 34.6901, "lon": 135.1955},
    {"id": "nara", "name": "奈良市", "lat": 34.6851, "lon": 135.8328},
    {"id": "wakayama", "name": "和歌山市", "lat": 34.2260, "lon": 135.1675},
    {"id": "tottori", "name": "鳥取市", "lat": 35.5036, "lon": 134.2383},
    {"id": "matsue", "name": "松江市", "lat": 35.4723, "lon": 133.0505},
    {"id": "okayama", "name": "岡山市", "lat": 34.6618, "lon": 133.9350},
    {"id": "hiroshima", "name": "広島市", "lat": 34.3853, "lon": 132.4553},
    {"id": "yamaguchi", "name": "山口市", "lat": 34.1859, "lon": 131.4714},
    {"id": "tokushima", "name": "徳島市", "lat": 34.0658, "lon": 134.5594},
    {"id": "takamatsu", "name": "高松市", "lat": 34.3401, "lon": 134.0434},
    {"id": "matsuyama", "name": "松山市", "lat": 33.8392, "lon": 132.7656},
    {"id": "kochi", "name": "高知市", "lat": 33.5597, "lon": 133.5311},
    {"id": "fukuoka", "name": "福岡市", "lat": 33.5902, "lon": 130.4017},
    {"id": "saga", "name": "佐賀市", "lat": 33.2494, "lon": 130.2989},
    {"id": "nagasaki", "name": "長崎市", "lat": 32.7503, "lon": 129.8779},
    {"id": "kumamoto", "name": "熊本市", "lat": 32.7898, "lon": 130.7417},
    {"id": "oita", "name": "大分市", "lat": 33.2382, "lon": 131.6126},
    {"id": "miyazaki", "name": "宮崎市", "lat": 31.9111, "lon": 131.4239},
    {"id": "kagoshima", "name": "鹿児島市", "lat": 31.5602, "lon": 130.5581},
    {"id": "naha", "name": "那覇市", "lat": 26.2124, "lon": 127.6809},
]

TZ = "Asia/Tokyo"
VARS = "temperature_2m_max,temperature_2m_min,temperature_2m_mean,weather_code,precipitation_sum"


def fetch_json_with_retry(url, retries=3, delay=2):
  for i in range(retries):
    try:
      req = urllib.request.Request(url, headers={"User-Agent": "WeatherBot/1.0"})
      with urllib.request.urlopen(req, timeout=15) as res:
        return json.loads(res.read().decode("utf-8"))
    except Exception as e:
      if i == retries - 1:
        raise e
      time.sleep(delay)


def parse_daily(daily):
  if not daily or "time" not in daily:
    return {}
  out = {}
  times = daily["time"]
  for i, d in enumerate(times):
    out[d] = {
        "date": d,
        "t_max": daily["temperature_2m_max"][i]
        if "temperature_2m_max" in daily
        else None,
        "t_min": daily["temperature_2m_min"][i]
        if "temperature_2m_min" in daily
        else None,
        "t_mean": daily["temperature_2m_mean"][i]
        if "temperature_2m_mean" in daily
        else None,
        "weather_code": daily["weather_code"][i]
        if "weather_code" in daily
        else None,
        "precip": daily["precipitation_sum"][i]
        if "precipitation_sum" in daily
        else None,
    }
  return out


def main():
  jst = timezone(timedelta(hours=9))
  today = datetime.now(jst)

  end_date = today - timedelta(days=365)
  start_date = end_date - timedelta(days=400)

  all_data = {}

  for city in CITIES:
    print(f"取得中: {city['name']} ({city['id']})...")
    try:
      recent_url = f"https://api.open-meteo.com/v1/forecast?latitude={city['lat']}&longitude={city['lon']}&daily={VARS}&timezone={TZ}&past_days=40&forecast_days=1"
      recent_res = fetch_json_with_retry(recent_url)

      ly_url = f"https://historical-forecast-api.open-meteo.com/v1/forecast?latitude={city['lat']}&longitude={city['lon']}&daily={VARS}&timezone={TZ}&start_date={start_date.strftime('%Y-%m-%d')}&end_date={end_date.strftime('%Y-%m-%d')}"
      ly_res = fetch_json_with_retry(ly_url)

      merged = {
          **parse_daily(ly_res.get("daily")),
          **parse_daily(recent_res.get("daily")),
      }
      all_data[city["id"]] = merged
      time.sleep(0.2)  # 連続リクエストの間隔を短縮
    except Exception as e:
      print(代 := f"⚠️ {city['name']} の取得に失敗しましたがスキップします: {e}")
      all_data[city["id"]] = {}

  os.makedirs("data", exist_ok=True)
  with open("data/weather.json", "w", encoding="utf-8") as f:
    json.dump(all_data, f, ensure_ascii=False, separators=(",", ":"))
  print("✅ data/weather.json の保存が完了しました。")


if __name__ == "__main__":
  main()
