#!/usr/bin/env python3
"""
Pre-GitHub Push Verification Checklist
Verifies system is ready for deployment
"""

import os
import json
import subprocess
import requests
import time
import sys

class PreDeploymentChecker:
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
    
    def check(self, description, condition):
        """Print check result"""
        if condition:
            print(f"✅ {description}")
            self.checks_passed += 1
        else:
            print(f"❌ {description}")
            self.checks_failed += 1
    
    def file_exists(self, path):
        return os.path.exists(path)
    
    def file_size_kb(self, path):
        if os.path.exists(path):
            return os.path.getsize(path) / 1024
        return 0
    
    def run_checks(self):
        print("\n" + "="*70)
        print("📋 PRE-GITHUB PUSH VERIFICATION CHECKLIST")
        print("="*70)
        
        # ========== FILE STRUCTURE CHECKS ==========
        print("\n📁 FILE STRUCTURE")
        print("-" * 70)
        
        self.check("api.py exists", self.file_exists("api.py"))
        self.check("requirements.txt exists", self.file_exists("requirements.txt"))
        self.check("README.md exists", self.file_exists("README.md"))
        self.check("frontend.html exists", self.file_exists("frontend.html"))
        self.check("eda.html exists", self.file_exists("eda.html"))
        self.check("data/Metro_Interstate_Traffic_Volume.csv exists", 
                   self.file_exists("data/Metro_Interstate_Traffic_Volume.csv"))
        self.check("models/ directory exists", os.path.isdir("models"))
        
        # ========== MODEL PERSISTENCE CHECKS ==========
        print("\n💾 MODEL PERSISTENCE")
        print("-" * 70)
        
        model_exists = self.file_exists("model.pkl")
        scaler_exists = self.file_exists("scaler.pkl")
        
        self.check("model.pkl exists (trained model)", model_exists)
        self.check("scaler.pkl exists (fitted scaler)", scaler_exists)
        
        if model_exists:
            model_size = self.file_size_kb("model.pkl")
            self.check(f"model.pkl size reasonable ({model_size:.1f} KB > 100 KB)", model_size > 100)
        
        if scaler_exists:
            scaler_size = self.file_size_kb("scaler.pkl")
            self.check(f"scaler.pkl size reasonable ({scaler_size:.1f} KB > 0.5 KB)", scaler_size > 0.5)
        
        # ========== API FUNCTIONALITY CHECKS ==========
        print("\n🔧 API FUNCTIONALITY")
        print("-" * 70)
        
        # Start API in background
        proc = subprocess.Popen(
            ['python', 'api.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(3)
        
        try:
            # Check if API is running
            try:
                response = requests.get('http://localhost:5000/api/overview', timeout=3)
                api_running = response.status_code == 200
            except:
                api_running = False
            
            self.check("API server responds on port 5000", api_running)
            
            if api_running:
                # Test endpoints
                endpoints_to_test = [
                    '/api/overview',
                    '/api/feature_importance',
                    '/api/peak_windows',
                    '/api/patterns',
                    '/api/weather',
                    '/api/heatmap',
                    '/api/congestion_risk',
                ]
                
                endpoints_working = 0
                for endpoint in endpoints_to_test:
                    try:
                        resp = requests.get(f'http://localhost:5000{endpoint}', timeout=3)
                        if resp.status_code == 200:
                            endpoints_working += 1
                    except:
                        pass
                
                self.check(f"GET endpoints working ({endpoints_working}/7)", endpoints_working == 7)
                
                # Test POST endpoints
                try:
                    resp = requests.post(
                        'http://localhost:5000/api/predict',
                        json={'hour':8,'dow':1,'month':6,'temp_c':20,'rain':0,'snow':0,'clouds':40,'weather':'Clear'},
                        timeout=3
                    )
                    self.check("POST /api/predict working", resp.status_code == 200)
                except:
                    self.check("POST /api/predict working", False)
                
                try:
                    resp = requests.post(
                        'http://localhost:5000/api/forecast24',
                        json={'dow':1,'month':6,'temp_c':20,'rain':0,'snow':0,'clouds':40,'weather':'Clear'},
                        timeout=3
                    )
                    self.check("POST /api/forecast24 working", resp.status_code == 200)
                except:
                    self.check("POST /api/forecast24 working", False)
                
                # Check response format
                try:
                    resp = requests.get('http://localhost:5000/api/overview')
                    data = resp.json()
                    required_keys = ['hourly_avg', 'peak_hour', 'peak_volume', 'avg_volume', 'model_r2', 'model_mae']
                    has_all_keys = all(k in data for k in required_keys)
                    self.check("API response format is correct", has_all_keys)
                except:
                    self.check("API response format is correct", False)
        
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except:
                proc.kill()
        
        # ========== FRONTEND FILES CHECKS ==========
        print("\n🌐 FRONTEND FILES")
        print("-" * 70)
        
        frontend_files = [
            'frontend.html',
            'eda.html',
            'evaluation.html',
            'features.html',
            'map_page.html',
        ]
        
        for fname in frontend_files:
            exists = self.file_exists(fname)
            size = self.file_size_kb(fname) if exists else 0
            self.check(f"{fname:25} ({size:6.1f} KB)", exists)
        
        # ========== CODE QUALITY CHECKS ==========
        print("\n📝 CODE QUALITY")
        print("-" * 70)
        
        # Check api.py
        with open('api.py', 'r') as f:
            api_code = f.read()
            
            self.check("api.py contains model persistence (joblib.load)", 
                       "joblib.load" in api_code)
            self.check("api.py contains X_scaled training", 
                       "X_scaled" in api_code and "model.fit(X_scaled" in api_code)
            self.check("api.py contains rain outlier removal", 
                       "rain_1h" in api_code and "< 500" in api_code)
            self.check("api.py contains snow outlier removal", 
                       "snow_1h" in api_code and "< 5" in api_code)
            self.check("api.py has CORS enabled", 
                       "CORS" in api_code or "Access-Control" in api_code)
        
        # Check for credentials in code
        with open('api.py', 'r') as f:
            api_code = f.read()
            has_creds = any(x in api_code.lower() for x in ['password=', 'api_key=', 'secret='])
            self.check("No hardcoded credentials in api.py", not has_creds)
        
        # Check requirements.txt
        req_exists = self.file_exists("requirements.txt")
        self.check("requirements.txt exists", req_exists)
        
        if req_exists:
            with open('requirements.txt', 'r') as f:
                req_content = f.read()
                required_packages = ['flask', 'xgboost', 'pandas', 'scikit-learn', 'joblib']
                for pkg in required_packages:
                    self.check(f"requirements.txt includes {pkg}", pkg.lower() in req_content.lower())
        
        # ========== SUMMARY ==========
        print("\n" + "="*70)
        print("📊 SUMMARY")
        print("="*70)
        
        total = self.checks_passed + self.checks_failed
        percentage = (self.checks_passed / total * 100) if total > 0 else 0
        
        print(f"Passed: {self.checks_passed}/{total}")
        print(f"Failed: {self.checks_failed}/{total}")
        print(f"Score:  {percentage:.1f}%")
        
        if self.checks_failed == 0:
            print("\n🎉 ALL CHECKS PASSED - READY FOR GITHUB!")
            print("\nNext steps:")
            print("  1. git add .")
            print("  2. git commit -m 'Production ready: ML model persistence, fixed preprocessing, full-stack tested'")
            print("  3. git push origin main")
            return True
        else:
            print(f"\n⚠️  {self.checks_failed} CHECK(S) FAILED - REVIEW REQUIRED")
            return False

if __name__ == '__main__':
    checker = PreDeploymentChecker()
    ready = checker.run_checks()
    sys.exit(0 if ready else 1)
