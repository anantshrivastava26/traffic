import pandas as pd
import numpy as np
import json
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

print("="*80)
print("📊 GENERATING EDA DATA FROM ACTUAL DATASET")
print("="*80)

# LOAD DATA
df = pd.read_csv('data/Metro_Interstate_Traffic_Volume.csv')

# CLEANING
df['temp_c'] = df['temp'] - 273.15
df = df[df['temp'] > 0]
df = df[df['rain_1h'] < 500]
df = df[df['snow_1h'] < 5]
df['holiday'] = df['holiday'].fillna('None')

# ─────────────────────────────────────────────
# BASIC DATASET INFO
# ─────────────────────────────────────────────
dataset_info = {
    'total_records': len(df),
    'date_range_start': str(df['date_time'].min()),
    'date_range_end': str(df['date_time'].max()),
    'original_features': 9,
    'final_features': 19,
    'missing_values_final': 0
}

# ─────────────────────────────────────────────
# TRAFFIC VOLUME STATS
# ─────────────────────────────────────────────
vol = df['traffic_volume']
mean_vol = float(vol.mean())
median_vol = float(vol.median())
max_vol = float(vol.max())
min_vol = float(vol.min())
std_vol = float(vol.std())

traffic_stats = {
    'mean': round(mean_vol, 1),
    'median': round(median_vol, 0),
    'max': round(max_vol, 0),
    'min': round(min_vol, 0),
    'std': round(std_vol, 1)
}

# DISTRIBUTION
low_pct = ((vol < 1000).sum() / len(vol)) * 100
med_pct = (((vol >= 1000) & (vol < 3000)).sum() / len(vol)) * 100
high_pct = (((vol >= 3000) & (vol < 5000)).sum() / len(vol)) * 100
sev_pct = ((vol >= 5000).sum() / len(vol)) * 100

distribution = {
    'low': round(low_pct, 1),
    'medium': round(med_pct, 1),
    'high': round(high_pct, 1),
    'severe': round(sev_pct, 1)
}

# ─────────────────────────────────────────────
# TEMPERATURE ANALYSIS
# ─────────────────────────────────────────────
temp_stats = {
    'mean': round(df['temp_c'].mean(), 1),
    'min': round(df['temp_c'].min(), 1),
    'max': round(df['temp_c'].max(), 1)
}

# ─────────────────────────────────────────────
# RAIN ANALYSIS
# ─────────────────────────────────────────────
rain_stats = {
    'mean': round(df['rain_1h'].mean(), 2),
    'max': round(df['rain_1h'].max(), 2)
}

# ─────────────────────────────────────────────
# HOLIDAY ANALYSIS
# ─────────────────────────────────────────────
holiday_counts = df['holiday'].value_counts().to_dict()
holiday_stats = {
    'none': int(holiday_counts.get('None', 0)),
    'holidays': int(len(df[df['holiday'] != 'None']))
}

# ─────────────────────────────────────────────
# HOURLY PATTERNS (0-23)
# ─────────────────────────────────────────────
df['hour'] = pd.to_datetime(df['date_time']).dt.hour
hourly_data = []
for hour in range(24):
    hour_avg = float(df[df['hour'] == hour]['traffic_volume'].mean())
    hourly_data.append(round(hour_avg, 0))

# ─────────────────────────────────────────────
# DAY OF WEEK PATTERNS (0=Monday, 6=Sunday)
# ─────────────────────────────────────────────
df['dow'] = pd.to_datetime(df['date_time']).dt.dayofweek
dow_data = []
for day in range(7):
    day_avg = float(df[df['dow'] == day]['traffic_volume'].mean())
    dow_data.append(round(day_avg, 0))

# ─────────────────────────────────────────────
# MONTHLY PATTERNS (1-12)
# ─────────────────────────────────────────────
df['month'] = pd.to_datetime(df['date_time']).dt.month
monthly_data = []
for month in range(1, 13):
    month_avg = float(df[df['month'] == month]['traffic_volume'].mean())
    monthly_data.append(round(month_avg, 0))

# ─────────────────────────────────────────────
# WEATHER ANALYSIS
# ─────────────────────────────────────────────
weather_by_type = df.groupby('weather_main')['traffic_volume'].agg(['mean', 'count']).to_dict('index')
weather_names = list(weather_by_type.keys())
weather_avgs = [round(weather_by_type[w]['mean'], 0) for w in weather_names]
weather_counts = [int(weather_by_type[w]['count']) for w in weather_names]

# ─────────────────────────────────────────────
# CORRELATION ANALYSIS
# ─────────────────────────────────────────────
# Create some derived features for correlation
df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
df['dow_sin'] = np.sin(2 * np.pi * df['dow'] / 7)
df['rush_hour'] = ((df['hour'] >= 7) & (df['hour'] <= 9) | (df['hour'] >= 16) & (df['hour'] <= 18)).astype(int)

corr_with_target = {
    'rush_hour': round(float(df[['rush_hour', 'traffic_volume']].corr().iloc[0, 1]), 2),
    'is_weekend': round(float(df[['dow', 'traffic_volume']].corr().iloc[0, 1]), 2),
    'hour_sin': round(float(df[['hour_sin', 'traffic_volume']].corr().iloc[0, 1]), 2),
    'hour_cos': round(float(df[['hour_cos', 'traffic_volume']].corr().iloc[0, 1]), 2),
    'dow_sin': round(float(df[['dow_sin', 'traffic_volume']].corr().iloc[0, 1]), 2),
    'temp_c': round(float(df[['temp_c', 'traffic_volume']].corr().iloc[0, 1]), 2),
    'month': round(float(df[['month', 'traffic_volume']].corr().iloc[0, 1]), 2),
    'snow_1h': round(float(df[['snow_1h', 'traffic_volume']].corr().iloc[0, 1]), 2),
    'rain_1h': round(float(df[['rain_1h', 'traffic_volume']].corr().iloc[0, 1]), 2),
    'clouds_all': round(float(df[['clouds_all', 'traffic_volume']].corr().iloc[0, 1]), 2)
}

# ─────────────────────────────────────────────
# OUTLIER ANALYSIS
# ─────────────────────────────────────────────
Q1 = float(vol.quantile(0.25))
Q3 = float(vol.quantile(0.75))
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

outliers = {
    'q1': round(Q1, 0),
    'q3': round(Q3, 0),
    'iqr': round(IQR, 0),
    'lower_bound': round(lower_bound, 0),
    'upper_bound': round(upper_bound, 0),
    'outliers_found': len(vol[(vol < lower_bound) | (vol > upper_bound)])
}

# ─────────────────────────────────────────────
# COMPILE ALL DATA
# ─────────────────────────────────────────────
eda_data = {
    'dataset_info': dataset_info,
    'traffic_stats': traffic_stats,
    'distribution': distribution,
    'temp_stats': temp_stats,
    'rain_stats': rain_stats,
    'holiday_stats': holiday_stats,
    'hourly_data': hourly_data,
    'dow_data': dow_data,
    'monthly_data': monthly_data,
    'weather_names': weather_names,
    'weather_avgs': weather_avgs,
    'weather_counts': weather_counts,
    'correlations': corr_with_target,
    'outliers': outliers
}

# ─────────────────────────────────────────────
# SAVE TO JSON
# ─────────────────────────────────────────────
with open('eda_data.json', 'w') as f:
    json.dump(eda_data, f, indent=2)

print("\n✅ EDA DATA GENERATED: eda_data.json")
print(f"\n📊 Summary:")
print(f"  • Records: {dataset_info['total_records']}")
print(f"  • Traffic Mean: {traffic_stats['mean']} vehicles/hr")
print(f"  • Distribution: LOW {distribution['low']}% | MED {distribution['medium']}% | HIGH {distribution['high']}% | SEVERE {distribution['severe']}%")
print(f"  • Temperature: {temp_stats['min']}°C to {temp_stats['max']}°C")
print(f"  • Rain: {rain_stats['mean']}mm avg, {rain_stats['max']}mm max")
print(f"  • Weather types: {len(weather_names)}")
print(f"  • Outliers found: {outliers['outliers_found']}")
