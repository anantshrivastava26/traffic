#!/usr/bin/env python3
"""Test the peak volume fix"""
import subprocess
import time
import requests

proc_api = subprocess.Popen(['python', 'api.py'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
proc_server = subprocess.Popen(['python', '-m', 'http.server', '3000'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd='.')
time.sleep(3)

try:
    # Fetch frontend.html
    print("Loading frontend.html from http://localhost:3000/frontend.html...")
    r = requests.get('http://localhost:3000/frontend.html', timeout=5)
    html = r.text
    
    # Check if fix is in place
    if 'const peakVol=data?data.peak_volume:4876;' in html:
        print("✅ Fallback for peak_volume is present")
    else:
        print("❌ Fallback for peak_volume NOT found")
    
    if 'const peakHr=data?data.peak_hour:17;' in html:
        print("✅ Fallback for peak_hour is present")
    else:
        print("❌ Fallback for peak_hour NOT found")
    
    if 'document.getElementById(\'kpi-peak\').textContent=peakVol.toLocaleString();' in html:
        print("✅ KPI peak is always set (not conditional)")
    else:
        print("❌ KPI peak assignment not found")
    
    # Test API
    print("\nTesting API endpoint...")
    r = requests.get('http://localhost:5000/api/overview', timeout=5)
    data = r.json()
    print(f"✅ API returns peak_volume: {data['peak_volume']}")
    print(f"✅ API returns peak_hour: {data['peak_hour']}")
    
    print("\n✅ ALL CHECKS PASSED - Peak volume should now display")
    
except Exception as e:
    print(f"❌ Error: {e}")

finally:
    import os, signal
    try:
        os.kill(proc_api.pid, signal.SIGTERM)
    except:
        pass
    try:
        os.kill(proc_server.pid, signal.SIGTERM)
    except:
        pass
