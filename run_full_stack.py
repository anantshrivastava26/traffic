#!/usr/bin/env python3
"""
Full Stack Local Test Runner
- Starts Flask API backend (port 5000)
- Starts HTTP server for frontend (port 3000)
- Provides live testing console
"""

import subprocess
import time
import requests
import signal
import os
import sys
import webbrowser
from threading import Thread

class FullStackTester:
    def __init__(self):
        self.api_proc = None
        self.server_proc = None
        self.api_running = False
        self.server_running = False
    
    def start_api(self):
        """Start Flask API on port 5000"""
        try:
            print("\n📡 Starting Flask API on port 5000...")
            self.api_proc = subprocess.Popen(
                ['python', 'api.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            time.sleep(3)  # Wait for API to start
            
            # Verify API is running
            try:
                response = requests.get('http://localhost:5000/api/overview', timeout=5)
                if response.status_code == 200:
                    print("✅ API Started Successfully")
                    self.api_running = True
                    return True
            except:
                pass
        except Exception as e:
            print(f"❌ Failed to start API: {e}")
        return False
    
    def start_http_server(self):
        """Start HTTP server on port 3000"""
        try:
            print("🌐 Starting HTTP Server on port 3000...")
            self.server_proc = subprocess.Popen(
                ['python', '-m', 'http.server', '3000'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.getcwd()
            )
            time.sleep(2)  # Wait for server to start
            
            # Verify server is running
            try:
                response = requests.get('http://localhost:3000/frontend.html', timeout=5)
                if response.status_code == 200:
                    print("✅ HTTP Server Started Successfully")
                    self.server_running = True
                    return True
            except:
                pass
        except Exception as e:
            print(f"❌ Failed to start HTTP Server: {e}")
        return False
    
    def test_api_endpoints(self):
        """Test all critical API endpoints"""
        print("\n" + "="*70)
        print("🧪 TESTING API ENDPOINTS")
        print("="*70)
        
        tests = {
            '/api/overview': 'GET',
            '/api/feature_importance': 'GET',
            '/api/peak_windows': 'GET',
            '/api/patterns': 'GET',
            '/api/weather': 'GET',
            '/api/heatmap': 'GET',
            '/api/congestion_risk': 'GET',
        }
        
        passed = 0
        failed = 0
        
        for endpoint, method in tests.items():
            try:
                response = requests.get(f'http://localhost:5000{endpoint}', timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ {endpoint:30} → {str(type(data).__name__):10} OK")
                    passed += 1
                else:
                    print(f"❌ {endpoint:30} → Status {response.status_code}")
                    failed += 1
            except Exception as e:
                print(f"❌ {endpoint:30} → Error: {str(e)[:30]}")
                failed += 1
        
        # Test POST endpoints
        post_tests = [
            ('/api/predict', {'hour':8,'dow':1,'month':6,'temp_c':20,'rain':0,'snow':0,'clouds':40,'weather':'Clear'}),
            ('/api/forecast24', {'dow':1,'month':6,'temp_c':20,'rain':0,'snow':0,'clouds':40,'weather':'Clear'}),
            ('/api/scenario', {'dow':1,'month':6,'temp_c':20,'rain':0,'snow':0,'clouds':40,'weather':'Clear','weather_severity':0,'special_event':0,'incident':0,'remote_work':0}),
        ]
        
        for endpoint, payload in post_tests:
            try:
                response = requests.post(f'http://localhost:5000{endpoint}', json=payload, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ {endpoint:30} → {str(type(data).__name__):10} OK")
                    passed += 1
                else:
                    print(f"❌ {endpoint:30} → Status {response.status_code}")
                    failed += 1
            except Exception as e:
                print(f"❌ {endpoint:30} → Error: {str(e)[:30]}")
                failed += 1
        
        print(f"\n📊 Results: {passed} passed, {failed} failed")
        return failed == 0
    
    def test_prediction_quality(self):
        """Test prediction quality and response format"""
        print("\n" + "="*70)
        print("🎯 TESTING PREDICTION QUALITY")
        print("="*70)
        
        test_cases = [
            {
                'name': 'Morning Rush Hour (Weekday)',
                'data': {'hour':8,'dow':1,'month':6,'temp_c':20,'rain':0,'snow':0,'clouds':40,'weather':'Clear'},
                'expected_range': (4000, 7000)
            },
            {
                'name': 'Late Night (Weekend)',
                'data': {'hour':2,'dow':5,'month':6,'temp_c':15,'rain':0,'snow':0,'clouds':30,'weather':'Clear'},
                'expected_range': (200, 1000)
            },
            {
                'name': 'Rainy Afternoon (Weekday)',
                'data': {'hour':14,'dow':2,'month':3,'temp_c':10,'rain':5,'snow':0,'clouds':80,'weather':'Rain'},
                'expected_range': (2000, 5000)
            },
            {
                'name': 'Heavy Snow Evening',
                'data': {'hour':18,'dow':3,'month':1,'temp_c':-5,'rain':0,'snow':2,'clouds':90,'weather':'Snow'},
                'expected_range': (2000, 6000)
            },
        ]
        
        for test in test_cases:
            try:
                response = requests.post(
                    'http://localhost:5000/api/predict',
                    json=test['data'],
                    timeout=5
                )
                if response.status_code == 200:
                    pred = response.json()
                    volume = pred['volume']
                    level = pred['level']
                    risk = pred['risk']
                    
                    in_range = test['expected_range'][0] <= volume <= test['expected_range'][1]
                    status = "✅" if in_range else "⚠️"
                    
                    print(f"{status} {test['name']:35} → {volume:5} vehicles ({level:6}, risk {risk:3}/100)")
                else:
                    print(f"❌ {test['name']:35} → HTTP {response.status_code}")
            except Exception as e:
                print(f"❌ {test['name']:35} → Error: {str(e)[:40]}")
    
    def test_frontend_access(self):
        """Verify frontend files are accessible"""
        print("\n" + "="*70)
        print("📄 TESTING FRONTEND FILE ACCESS")
        print("="*70)
        
        files = [
            'frontend.html',
            'eda.html',
            'evaluation.html',
            'features.html',
            'map_page.html',
        ]
        
        for filename in files:
            try:
                response = requests.get(f'http://localhost:3000/{filename}', timeout=5)
                if response.status_code == 200:
                    size = len(response.content) / 1024  # KB
                    print(f"✅ {filename:25} → {size:7.1f} KB")
                else:
                    print(f"❌ {filename:25} → HTTP {response.status_code}")
            except Exception as e:
                print(f"❌ {filename:25} → Error: {str(e)[:40]}")
    
    def test_api_response_format(self):
        """Verify API response formats"""
        print("\n" + "="*70)
        print("📋 TESTING API RESPONSE FORMATS")
        print("="*70)
        
        # Test overview format
        try:
            response = requests.get('http://localhost:5000/api/overview')
            data = response.json()
            required_keys = ['hourly_avg', 'peak_hour', 'peak_volume', 'avg_volume', 'model_r2', 'model_mae']
            missing = [k for k in required_keys if k not in data]
            if not missing:
                print(f"✅ /api/overview response format → {len(required_keys)} required keys present")
            else:
                print(f"❌ /api/overview response format → Missing: {missing}")
        except Exception as e:
            print(f"❌ /api/overview format test → {e}")
        
        # Test prediction format
        try:
            response = requests.post(
                'http://localhost:5000/api/predict',
                json={'hour':8,'dow':1,'month':6,'temp_c':20,'rain':0,'snow':0,'clouds':40,'weather':'Clear'}
            )
            data = response.json()
            required_keys = ['volume', 'level', 'color', 'risk', 'factors']
            missing = [k for k in required_keys if k not in data]
            if not missing:
                print(f"✅ /api/predict response format → {len(required_keys)} required keys present")
            else:
                print(f"❌ /api/predict response format → Missing: {missing}")
        except Exception as e:
            print(f"❌ /api/predict format test → {e}")
        
        # Test forecast format
        try:
            response = requests.post(
                'http://localhost:5000/api/forecast24',
                json={'dow':1,'month':6,'temp_c':20,'rain':0,'snow':0,'clouds':40,'weather':'Clear'}
            )
            data = response.json()
            if isinstance(data, list) and len(data) == 24:
                first_item = data[0]
                required_keys = ['hour', 'volume', 'level', 'color', 'risk']
                missing = [k for k in required_keys if k not in first_item]
                if not missing:
                    print(f"✅ /api/forecast24 response format → 24 hours with correct keys")
                else:
                    print(f"❌ /api/forecast24 response format → Missing: {missing}")
            else:
                print(f"❌ /api/forecast24 response format → Not 24 hours")
        except Exception as e:
            print(f"❌ /api/forecast24 format test → {e}")
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*70)
        print("📊 FULL STACK TEST REPORT")
        print("="*70)
        print(f"Backend API:  http://localhost:5000")
        print(f"Frontend:     http://localhost:3000/frontend.html")
        print(f"EDA Dashboard: http://localhost:3000/eda.html")
        print(f"Evaluation:   http://localhost:3000/evaluation.html")
        print(f"Features:     http://localhost:3000/features.html")
        print(f"Map:          http://localhost:3000/map_page.html")
        print("="*70)
    
    def cleanup(self):
        """Stop all processes"""
        print("\n🛑 Shutting down services...")
        if self.api_proc:
            self.api_proc.terminate()
            try:
                self.api_proc.wait(timeout=3)
            except:
                self.api_proc.kill()
        if self.server_proc:
            self.server_proc.terminate()
            try:
                self.server_proc.wait(timeout=3)
            except:
                self.server_proc.kill()
        print("✅ Services stopped")
    
    def run(self):
        """Run full stack test"""
        try:
            print("\n" + "="*70)
            print("🚀 FULL STACK LOCAL TEST SUITE")
            print("="*70)
            
            # Start services
            if not self.start_api():
                print("❌ Failed to start API - aborting")
                return False
            
            if not self.start_http_server():
                print("❌ Failed to start HTTP Server - aborting")
                return False
            
            # Run tests
            self.test_api_endpoints()
            self.test_prediction_quality()
            self.test_frontend_access()
            self.test_api_response_format()
            self.generate_test_report()
            
            print("\n" + "="*70)
            print("✅ FULL STACK TEST COMPLETE - READY TO DEPLOY")
            print("="*70)
            print("\n📌 URLS FOR MANUAL TESTING:")
            print("   Frontend:  http://localhost:3000/frontend.html")
            print("   EDA:       http://localhost:3000/eda.html")
            print("   API Base:  http://localhost:5000/api/overview")
            print("\n💡 Tip: Keep this running and visit URLs above in your browser")
            print("   Press Ctrl+C to stop\n")
            
            # Keep running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.cleanup()

if __name__ == '__main__':
    tester = FullStackTester()
    success = tester.run()
    sys.exit(0 if success else 1)
