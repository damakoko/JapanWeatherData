#!/usr/bin/env python3
"""Fetch current weather for Japan's 47 prefectural capitals.

Requires Python 3.11+; standard library only.
"""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# Coordinates are approximate city-centre positions (latitude, longitude).
LOCATIONS = [
    (1, '北海道', '札幌', 43.0618, 141.3545),
    (2, '青森県', '青森', 40.8244, 140.7400),
    (3, '岩手県', '盛岡', 39.7019, 141.1545),
    (4, '宮城県', '仙台', 38.2682, 140.8694),
    (5, '秋田県', '秋田', 39.7186, 140.1024),
    (6, '山形県', '山形', 38.2554, 140.3396),
    (7, '福島県', '福島', 37.7608, 140.4747),
    (8, '茨城県', '水戸', 36.3659, 140.4712),
    (9, '栃木県', '宇都宮', 36.5551, 139.8828),
    (10, '群馬県', '前橋', 36.3895, 139.0634),
    (11, '埼玉県', 'さいたま', 35.8617, 139.6455),
    (12, '千葉県', '千葉', 35.6074, 140.1065),
    (13, '東京都', '東京', 35.6895, 139.6917),
    (14, '神奈川県', '横浜', 35.4437, 139.6380),
    (15, '新潟県', '新潟', 37.9161, 139.0364),
    (16, '富山県', '富山', 36.6953, 137.2113),
    (17, '石川県', '金沢', 36.5613, 136.6562),
    (18, '福井県', '福井', 36.0641, 136.2196),
    (19, '山梨県', '甲府', 35.6623, 138.5684),
    (20, '長野県', '長野', 36.6485, 138.1948),
    (21, '岐阜県', '岐阜', 35.4233, 136.7607),
    (22, '静岡県', '静岡', 34.9756, 138.3828),
    (23, '愛知県', '名古屋', 35.1815, 136.9066),
    (24, '三重県', '津', 34.7303, 136.5086),
    (25, '滋賀県', '大津', 35.0179, 135.8546),
    (26, '京都府', '京都', 35.0116, 135.7681),
    (27, '大阪府', '大阪', 34.6937, 135.5023),
    (28, '兵庫県', '神戸', 34.6901, 135.1955),
    (29, '奈良県', '奈良', 34.6851, 135.8048),
    (30, '和歌山県', '和歌山', 34.2304, 135.1708),
    (31, '鳥取県', '鳥取', 35.5011, 134.2351),
    (32, '島根県', '松江', 35.4681, 133.0484),
    (33, '岡山県', '岡山', 34.6551, 133.9195),
    (34, '広島県', '広島', 34.3853, 132.4553),
    (35, '山口県', '山口', 34.1785, 131.4737),
    (36, '徳島県', '徳島', 34.0703, 134.5548),
    (37, '香川県', '高松', 34.3428, 134.0466),
    (38, '愛媛県', '松山', 33.8392, 132.7657),
    (39, '高知県', '高知', 33.5597, 133.5311),
    (40, '福岡県', '福岡', 33.5904, 130.4017),
    (41, '佐賀県', '佐賀', 33.2635, 130.3009),
    (42, '長崎県', '長崎', 32.7503, 129.8777),
    (43, '熊本県', '熊本', 32.8031, 130.7079),
    (44, '大分県', '大分', 33.2382, 131.6126),
    (45, '宮崎県', '宮崎', 31.9111, 131.4239),
    (46, '鹿児島県', '鹿児島', 31.5966, 130.5571),
    (47, '沖縄県', '那覇', 26.2124, 127.6809),
]

BASE_URL = 'https://api.open-meteo.com/v1/forecast'
OUT = Path(__file__).with_name('weather.json')


def fetch():
    params = {
        'latitude': ','.join(str(x[3]) for x in LOCATIONS),
        'longitude': ','.join(str(x[4]) for x in LOCATIONS),
        'current': 'temperature_2m,relative_humidity_2m,weather_code,precipitation,rain,snowfall,wind_speed_10m',
        'timezone': 'Asia/Tokyo',
        'forecast_days': '1',
    }
    req = Request(BASE_URL + '?' + urlencode(params), headers={'User-Agent': 'JapanWeatherData/1.0 (weather data prototype)'})
    with urlopen(req, timeout=45) as response:
        result = json.load(response)
    if not isinstance(result, list) or len(result) != len(LOCATIONS):
        raise ValueError(f'Expected {len(LOCATIONS)} locations; got {type(result).__name__} / {len(result) if isinstance(result, list) else "n/a"}')
    output = []
    for loc, item in zip(LOCATIONS, result):
        current = item.get('current', {})
        needed = ('temperature_2m', 'relative_humidity_2m', 'weather_code', 'precipitation', 'rain', 'snowfall', 'wind_speed_10m', 'time')
        if any(current.get(k) is None for k in needed):
            raise ValueError(f'Missing current weather data for {loc[2]}')
        output.append({
            'id': loc[0], 'prefecture': loc[1], 'city': loc[2],
            'weather_code': int(current['weather_code']),
            'temperature_c': float(current['temperature_2m']),
            'humidity_pct': int(current['relative_humidity_2m']),
            'precipitation_mm': float(current['precipitation']),
            'rain_mm': float(current['rain']),
            'snowfall_cm': float(current['snowfall']),
            'wind_kmh': float(current['wind_speed_10m']),
            'observed_at': current['time'] + '+09:00',
        })
    return {
        'schema_version': 1,
        'source': 'Open-Meteo',
        'updated_at': datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z'),
        'location_count': len(output),
        'locations': output,
    }


def main():
    if len(LOCATIONS) != 47 or len({x[0] for x in LOCATIONS}) != 47:
        raise ValueError('Location configuration must contain 47 unique IDs')
    for attempt in range(3):
        try:
            data = fetch()
            break
        except Exception as exc:
            if attempt == 2:
                raise
            print(f'Attempt {attempt + 1} failed: {exc}; retrying...', flush=True)
            time.sleep(10 * (attempt + 1))
    tmp = OUT.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    os.replace(tmp, OUT)
    print(f'Wrote {OUT} with {len(data["locations"])} locations')


if __name__ == '__main__':
    main()
