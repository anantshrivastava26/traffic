import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

print("="*80)
print("🔍 CLEAN EDA — Traffic Dataset")
print("="*80)

# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
df = pd.read_csv('data/Metro_Interstate_Traffic_Volume.csv')

# ─────────────────────────────────────────────
# CLEANING FIXES
# ─────────────────────────────────────────────

# 1. FIX TEMPERATURE (Kelvin → Celsius + invalid removal)
df['temp_c'] = df['temp'] - 273.15
df = df[df['temp'] > 0]   # remove invalid 0K rows

# 2. FIX RAIN OUTLIERS (remove unrealistic values)
df = df[df['rain_1h'] < 500]   # remove extreme outliers

# 3. FIX SNOW OUTLIERS
df = df[df['snow_1h'] < 5]

# 4. FIX HOLIDAY COLUMN
df['holiday'] = df['holiday'].fillna('None')

# ─────────────────────────────────────────────
# BASIC INFO
# ─────────────────────────────────────────────
print(f"\n📊 Shape: {df.shape}")
print(f"📅 Date Range: {df['date_time'].min()} → {df['date_time'].max()}")

# ─────────────────────────────────────────────
# TRAFFIC STATS
# ─────────────────────────────────────────────
vol = df['traffic_volume']

print("\n🚗 TRAFFIC STATS")
print(f"Mean: {vol.mean():.1f}")
print(f"Median: {vol.median():.0f}")
print(f"Max: {vol.max():.0f}")
print(f"Min: {vol.min():.0f}")

# ─────────────────────────────────────────────
# DISTRIBUTION
# ─────────────────────────────────────────────
low = (vol < 1000).mean()*100
med = ((vol >= 1000) & (vol < 3000)).mean()*100
high = ((vol >= 3000) & (vol < 5000)).mean()*100
sev = (vol >= 5000).mean()*100

print("\n📊 DISTRIBUTION")
print(f"LOW: {low:.1f}%")
print(f"MED: {med:.1f}%")
print(f"HIGH: {high:.1f}%")
print(f"SEVERE: {sev:.1f}%")

# ─────────────────────────────────────────────
# TEMP ANALYSIS (FIXED)
# ─────────────────────────────────────────────
print("\n🌡️ TEMPERATURE (CLEANED)")
print(f"Mean: {df['temp_c'].mean():.1f}°C")
print(f"Min: {df['temp_c'].min():.1f}°C")
print(f"Max: {df['temp_c'].max():.1f}°C")

# ─────────────────────────────────────────────
# RAIN ANALYSIS (FIXED)
# ─────────────────────────────────────────────
print("\n🌧️ RAIN (CLEANED)")
print(f"Mean: {df['rain_1h'].mean():.2f} mm")
print(f"Max: {df['rain_1h'].max():.2f} mm")

# ─────────────────────────────────────────────
# HOLIDAY ANALYSIS (FIXED)
# ─────────────────────────────────────────────
holiday_counts = df['holiday'].value_counts()

print("\n🎉 HOLIDAY (FIXED)")
print(f"None: {holiday_counts.get('None',0)}")
print(f"Holidays: {len(df[df['holiday']!='None'])}")

# ─────────────────────────────────────────────
# FINAL NOTE
# ─────────────────────────────────────────────
print("\n✅ CLEAN EDA COMPLETE")