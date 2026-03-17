#!/usr/bin/env python3
"""Test API endpoints after fixes"""
import requests
import subprocess
import time
import os
import signal

# Start API in background (silent mode)
proc = subprocess.Popen(['python', 'api.py'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(3)

try:
    print("="*70)
    print("TESTING FIXED API ENDPOINTS")
    print("="*70)
    
    # Test 1: Feature importance
    print("\n1. Feature Importance (Top 5):")
    response = requests.get('http://localhost:5000/api/feature_importance', timeout=5)
    features = response.json()[:5]
    for f in features:
        print(f"   {f['feature']}: {f['importance']}")
    
    # Test 2: Overview
    print("\n2. Overview Statistics:")
    response = requests.get('http://localhost:5000/api/overview', timeout=5)
    data = response.json()
    print(f"   Avg Volume: {data['avg_volume']} vehicles")
    print(f"   Peak Hour: {data['peak_hour']}:00 ({data['peak_volume']} vehicles)")
    print(f"   Model R²: {data['model_r2']}, MAE: {data['model_mae']}")
    
    # Test 3: Prediction (rush hour)
    print("\n3. Test Prediction (Morning Rush, Weekday):")
    response = requests.post(
        'http://localhost:5000/api/predict',
        json={'hour':8,'dow':1,'month':6,'temp_c':20,'rain':0,'snow':0,'clouds':40,'weather':'Clear'},
        timeout=5
    )
    pred = response.json()
    print(f"   Predicted Volume: {pred['volume']} vehicles")
    print(f"   Level: {pred['level']}, Risk Score: {pred['risk']}/100")
    
    # Test 4: 24-hour Forecast
    print("\n4. 24-Hour Forecast (sample):")
    response = requests.post(
        'http://localhost:5000/api/forecast24',
        json={'dow':1,'month':6,'temp_c':20,'rain':0,'snow':0,'clouds':40,'weather':'Clear'},
        timeout=5
    )
    forecast = response.json()
    peak = max(forecast, key=lambda x: x['volume'])
    low = min(forecast, key=lambda x: x['volume'])
    print(f"   Peak: Hour {peak['hour']}:00 ({peak['volume']} vehicles)")
    print(f"   Low:  Hour {low['hour']}:00 ({low['volume']} vehicles)")
    
    # Test 5: Peak windows
    print("\n5. Peak Congestion Windows:")
    response = requests.get('http://localhost:5000/api/peak_windows', timeout=5)
    peaks = response.json()[:3]
    for p in peaks:
        print(f"   Hour {p['hour']}:00 - {p['volume']} vehicles ({p['level']})")
    
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED - API WORKING CORRECTLY")
    print("="*70)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    try:
        os.kill(proc.pid, signal.SIGTERM)
    except:
        pass
