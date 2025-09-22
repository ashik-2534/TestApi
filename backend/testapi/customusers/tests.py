
"""
Comprehensive test script for Phase 2 security hardening
Tests throttling, authentication, and security features
"""

import requests
import time
import json
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


class SecurityTester:
    def __init__(self, base_url="http://127.0.0.1:8000/api/users"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {}
    
    def print_test_header(self, test_name):
        """Print formatted test header"""
        print(f"\n{'=' * 60}")
        print(f"Testing: {test_name}")
        print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
        print('=' * 60)
    
    def test_health_check(self):
        """Test basic connectivity"""
        self.print_test_header("API Health Check")
        
        try:
            response = self.session.get(f"{self.base_url}/users/health/")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API is healthy")
                print(f"   Status: {data.get('status')}")
                print(f"   Version: {data.get('version')}")
                print(f"   Debug Mode: {data.get('debug_mode')}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {str(e)}")
            return False
    
    def test_registration_throttling(self):
        """Test registration rate limiting"""
        self.print_test_header("Registration Throttling (3/min limit)")
        
        def register_attempt(i):
            data = {
                'username': f'testuser{i}_{int(time.time())}',
                'email': f'test{i}_{int(time.time())}@example.com',
                'password': 'testpass123',
                'password_confirm': 'testpass123',
                'first_name': f'Test{i}',
                'last_name': 'User'
            }
            
            try:
                response = self.session.post(f"{self.base_url}/users/auth/register/", json=data)
                return {
                    'attempt': i,
                    'status': response.status_code,
                    'success': response.status_code == 201,
                    'throttled': response.status_code == 429,
                    'response': response.text[:100]
                }
            except Exception as e:
                return {
                    'attempt': i,
                    'status': 'error',
                    'success': False,
                    'throttled': False,
                    'response': str(e)
                }
        
        # Try to register 5 users rapidly (should hit 3/min limit)
        attempts = []
        for i in range(5):
            result = register_attempt(i)
            attempts.append(result)
            print(f"   Attempt {i+1}: Status {result['status']} - {'Success' if result['success'] else 'Throttled' if result['throttled'] else 'Failed'}")
            time.sleep(0.5)  # Small delay between attempts
        
        successful = sum(1 for a in attempts if a['success'])
        throttled = sum(1 for a in attempts if a['throttled'])
        
        print(f"\nResults:")
        print(f"   Successful registrations: {successful}")
        print(f"   Throttled attempts: {throttled}")
        
        if throttled > 0:
            print("✅ Registration throttling is working")
            return True
        else:
            print("⚠️  Registration throttling may not be configured correctly")
            return False
    
    def test_login_throttling(self):
        """Test login rate limiting"""
        self.print_test_header("Login Throttling (5/min limit)")
        
        def login_attempt(i):
            data = {
                'username': f'nonexistent_user_{i}',
                'password': 'wrongpassword'
            }
            
            try:
                response = self.session.post(f"{self.base_url}/users/auth/login/", json=data)
                return {
                    'attempt': i,
                    'status': response.status_code,
                    'throttled': response.status_code == 429,
                    'response': response.text[:100]
                }
            except Exception as e:
                return {
                    'attempt': i,
                    'status': 'error',
                    'throttled': False,
                    'response': str(e)
                }
        
        # Try to login 8 times rapidly (should hit 5/min limit)
        attempts = []
        for i in range(8):
            result = login_attempt(i)
            attempts.append(result)
            print(f"   Attempt {i+1}: Status {result['status']} - {'Throttled' if result['throttled'] else 'Allowed'}")
            time.sleep(0.2)  # Small delay between attempts
        
        throttled = sum(1 for a in attempts if a['throttled'])
        
        print(f"\nResults:")
        print(f"   Throttled attempts: {throttled}")
        
        if throttled > 0:
            print("✅ Login throttling is working")
            return True
        else:
            print("⚠️  Login throttling may not be configured correctly")
            return False
    
    def test_concurrent_requests(self):
        """Test concurrent request handling"""
        self.print_test_header("Concurrent Request Handling")
        
        def make_request(i):
            try:
                start_time = time.time()
                response = self.session.get(f"{self.base_url}/users/users/")
                end_time = time.time()
                return {
                    'thread': i,
                    'status': response.status_code,
                    'response_time': round(end_time - start_time, 3),
                    'success': response.status_code == 200
                }
            except Exception as e:
                return {
                    'thread': i,
                    'status': 'error',
                    'response_time': 0,
                    'success': False,
                    'error': str(e)
                }
        
        # Make 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(10)]
            results = [future.result() for future in as_completed(futures)]
        
        successful = sum(1 for r in results if r['success'])
        avg_response_time = sum(r['response_time'] for r in results) / len(results)
        
        print(f"Results:")
        print(f"   Successful requests: {successful}/10")
        print(f"   Average response time: {avg_response_time:.3f}s")
        
        if successful >= 8:  # Allow for some failures
            print("✅ Concurrent request handling is working")
            return True
        else:
            print("❌ Concurrent request handling issues detected")
            return False
    
    def test_security_headers(self):
        """Test security headers in responses"""
        self.print_test_header("Security Headers Check")
        
        try:
            response = self.session.get(f"{self.base_url}/users/health/")
            headers = response.headers
            
            security_checks = {
                'Content-Type': 'application/json' in headers.get('Content-Type', ''),
                'X-Content-Type-Options': 'nosniff' in headers.get('X-Content-Type-Options', ''),
                'X-Frame-Options': headers.get('X-Frame-Options') in ['DENY', 'SAMEORIGIN'],
                'Referrer-Policy': bool(headers.get('Referrer-Policy')),
            }
            
            print("Security Headers:")
            for header, present in security_checks.items():
                status = "✅" if present else "❌"
                value = headers.get(header, 'Not set')
                print(f"   {status} {header}: {value}")
            
            passed = sum(security_checks.values())
            total = len(security_checks)
            
            if passed >= total * 0.5:  # At least 50% should pass
                print(f"✅ Security headers check passed ({passed}/{total})")
                return True
            else:
                print(f"⚠️  Security headers need improvement ({passed}/{total})")
                return False
                
        except Exception as e:
            print(f"❌ Security headers check failed: {str(e)}")
            return False
    
    def test_token_security(self):
        """Test JWT token security"""
        self.print_test_header("JWT Token Security")
        
        # First, create a test user
        user_data = {
            'username': f'tokentest_{int(time.time())}',
            'email': f'tokentest_{int(time.time())}@example.com',
            'password': 'securepass123',
            'password_confirm': 'securepass123'
        }
        
        try:
            # Register user
            reg_response = self.session.post(f"{self.base_url}/users/auth/register/", json=user_data)
            
            if reg_response.status_code != 201:
                print(f"❌ Could not create test user for token testing")
                return False
            
            tokens = reg_response.json().get('tokens', {})
            access_token = tokens.get('access')
            refresh_token = tokens.get('refresh')
            
            if not access_token or not refresh_token:
                print("❌ Tokens not received from registration")
                return False
            
            print("✅ Test user created and tokens received")
            
            # Test token verification
            verify_response = self.session.get(
                f"{self.base_url}/users/auth/verify/",
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            if verify_response.status_code == 200:
                print("✅ Token verification successful")
            else:
                print("❌ Token verification failed")
                return False
            
            # Test token refresh
            refresh_response = self.session.post(
                f"{self.base_url}/users/auth/refresh/",
                json={'refresh': refresh_token}
            )
            
            if refresh_response.status_code == 200:
                print("✅ Token refresh successful")
                new_tokens = refresh_response.json()
                new_access = new_tokens.get('access')
                
                if new_access and new_access != access_token:
                    print("✅ New access token generated")
                else:
                    print("⚠️  Access token may not have been rotated")
            else:
                print("❌ Token refresh failed")
                return False
            
            # Test logout (token blacklisting)
            logout_response = self.session.post(
                f"{self.base_url}/users/auth/logout/",
                json={'refresh': refresh_token},
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            if logout_response.status_code == 200:
                print("✅ Logout successful")
                
                # Try to use the old refresh token (should fail)
                old_refresh_response = self.session.post(
                    f"{self.base_url}/users/auth/refresh/",
                    json={'refresh': refresh_token}
                )
                
                if old_refresh_response.status_code != 200:
                    print("✅ Refresh token properly blacklisted after logout")
                    return True
                else:
                    print("⚠️  Refresh token blacklisting may not be working")
                    return False
            else:
                print("❌ Logout failed")
                return False
                
        except Exception as e:
            print(f"❌ Token security test failed: {str(e)}")
            return False
    
    def test_password_security(self):
        """Test password security requirements"""
        self.print_test_header("Password Security")
        
        weak_passwords = [
            'pass',           # Too short
            '12345678',       # Only numbers
            'password',       # Common password
            'abcdefgh',       # Only letters
            'Password',       # Missing complexity
        ]
        
        secure_passwords = [
            'SecurePass123!',
            'MyStr0ngP@ssw0rd',
            'C0mpl3xP@ssw0rd!'
        ]
        
        print("Testing weak passwords (should be rejected):")
        weak_rejected = 0
        for i, password in enumerate(weak_passwords):
            user_data = {
                'username': f'weaktest{i}_{int(time.time())}',
                'email': f'weaktest{i}_{int(time.time())}@example.com',
                'password': password,
                'password_confirm': password
            }
            
            try:
                response = self.session.post(f"{self.base_url}/users/auth/register/", json=user_data)
                if response.status_code != 201:
                    print(f"   ✅ '{password}' rejected")
                    weak_rejected += 1
                else:
                    print(f"   ❌ '{password}' accepted (should be rejected)")
            except Exception as e:
                print(f"   Error testing '{password}': {str(e)}")
        
        print(f"\nTesting secure passwords (should be accepted):")
        secure_accepted = 0
        for i, password in enumerate(secure_passwords):
            user_data = {
                'username': f'securetest{i}_{int(time.time())}',
                'email': f'securetest{i}_{int(time.time())}@example.com',
                'password': password,
                'password_confirm': password
            }
            
            try:
                response = self.session.post(f"{self.base_url}/users/auth/register/", json=user_data)
                if response.status_code == 201:
                    print(f"   ✅ '{password}' accepted")
                    secure_accepted += 1
                else:
                    print(f"   ❌ '{password}' rejected (should be accepted)")
            except Exception as e:
                print(f"   Error testing '{password}': {str(e)}")
        
        print(f"\nResults:")
        print(f"   Weak passwords rejected: {weak_rejected}/{len(weak_passwords)}")
        print(f"   Secure passwords accepted: {secure_accepted}/{len(secure_passwords)}")
        
        if weak_rejected >= len(weak_passwords) * 0.8 and secure_accepted >= len(secure_passwords) * 0.8:
            print("✅ Password security is working correctly")
            return True
        else:
            print("⚠️  Password security needs improvement")
            return False
    
    def run_all_tests(self):
        """Run all security tests"""
        print("🚀 Starting Phase 2 Security Testing")
        print(f"Target URL: {self.base_url}")
        
        tests = [
            ('Health Check', self.test_health_check),
            ('Registration Throttling', self.test_registration_throttling),
            ('Login Throttling', self.test_login_throttling),
            ('Concurrent Requests', self.test_concurrent_requests),
            ('Security Headers', self.test_security_headers),
            ('JWT Token Security', self.test_token_security),
            ('Password Security', self.test_password_security),
        ]
        
        results = {}
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                results[test_name] = result
                if result:
                    passed += 1
                time.sleep(1)  # Brief pause between tests
            except Exception as e:
                print(f"❌ {test_name} test failed with error: {str(e)}")
                results[test_name] = False
        
        # Final Summary
        print(f"\n{'=' * 60}")
        print("FINAL TEST SUMMARY")
        print('=' * 60)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All security tests passed! Your Phase 2 implementation is solid.")
        elif passed >= total * 0.8:
            print("✅ Most tests passed. Minor tweaks may be needed.")
        else:
            print("⚠️  Several tests failed. Review your Phase 2 implementation.")
        
        return results


def main():
    """Main function to run security tests"""
    import sys
    
    # Allow custom base URL
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    
    tester = SecurityTester(base_url)
    results = tester.run_all_tests()
    
    # Exit with error code if critical tests failed
    critical_tests = ['Health Check', 'JWT Token Security']
    critical_failed = any(not results.get(test, True) for test in critical_tests)
    
    if critical_failed:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()