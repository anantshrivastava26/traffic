#!/usr/bin/env python3
"""Test peak volume display issue"""
import subprocess
import time
import requests
import json

proc = subprocess.Popen(['python', 'api.py'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(3)

try:
    # Test 1: API response
    print("Testing API /overview endpoint...")
    r = requests.get('http://localhost:5000/api/overview', timeout=5)
    print(f"Status: {r.status_code}")
    data = r.json()
    
    print("\n✅ API Response contains:")
    print(f"   peak_volume: {data.get('peak_volume')} (type: {type(data.get('peak_volume')).__name__})")
    print(f"   peak_hour:   {data.get('peak_hour')} (type: {type(data.get('peak_hour')).__name__})")
    print(f"   avg_volume:  {data.get('avg_volume')}")
    print(f"   hourly_avg:  {len(data.get('hourly_avg', []))} hours")
    
    # Test 2: Check if values are None or empty
    if data.get('peak_volume') is None:
        print("\n❌ ERROR: peak_volume is None!")
    elif data.get('peak_volume') == 0:
        print("\n❌ ERROR: peak_volume is 0!")
    else:
        print(f"\n✅ Peak volume is valid: {data.get('peak_volume')}")
    
    # Test 3: Check CORS headers
    print("\nChecking CORS headers...")
    r2 = requests.get('http://localhost:5000/api/overview', 
                      headers={'Origin': 'http://localhost:3000'})
    print(f"Access-Control-Allow-Origin: {r2.headers.get('Access-Control-Allow-Origin', 'NOT SET')}")
    
    # Test 4: Detailed response
    print("\nFull API response:")
    print(json.dumps(data, indent=2))

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    import os, signal
    try:
        os.kill(proc.pid, signal.SIGTERM)
    except:
        pass
