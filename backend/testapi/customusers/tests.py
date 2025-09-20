from django.test import TestCase

# test_api_client.py
"""
Example client for testing JWT authentication with your API
Run this after setting up your Django server
"""

import requests
import json
from datetime import datetime


class APIClient:
    def __init__(self, base_url="http://127.0.0.1:8000/api"):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
        self.session = requests.Session()
    
    def set_auth_headers(self):
        """Set Authorization header with access token"""
        if self.access_token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}'
            })
    
    def register(self, username, email, password, **extra_fields):
        """Register a new user"""
        data = {
            'username': username,
            'email': email,
            'password': password,
            'password_confirm': password,
            **extra_fields
        }
        
        response = self.session.post(f"{self.base_url}/auth/register/", json=data)
        
        if response.status_code == 201:
            result = response.json()
            self.access_token = result['tokens']['access']
            self.refresh_token = result['tokens']['refresh']
            self.set_auth_headers()
            print(f"✅ Registered user: {result['user']['username']}")
            return result
        else:
            print(f"❌ Registration failed: {response.text}")
            return None
    
    def login(self, username, password):
        """Login with username/email and password"""
        data = {
            'username': username,
            'password': password
        }
        
        response = self.session.post(f"{self.base_url}/auth/login/", json=data)
        
        if response.status_code == 200:
            result = response.json()
            self.access_token = result['tokens']['access']
            self.refresh_token = result['tokens']['refresh']
            self.set_auth_headers()
            print(f"✅ Logged in as: {result['user']['username']}")
            return result
        else:
            print(f"❌ Login failed: {response.text}")
            return None
    
    def refresh_access_token(self):
        """Refresh the access token using refresh token"""
        if not self.refresh_token:
            print("❌ No refresh token available")
            return False
        
        data = {'refresh': self.refresh_token}
        response = self.session.post(f"{self.base_url}/auth/refresh/", json=data)
        
        if response.status_code == 200:
            result = response.json()
            self.access_token = result['access']
            if 'refresh' in result:
                self.refresh_token = result['refresh']
            self.set_auth_headers()
            print("✅ Token refreshed successfully")
            return True
        else:
            print(f"❌ Token refresh failed: {response.text}")
            return False
    
    def verify_token(self):
        """Verify if current token is valid"""
        response = self.session.get(f"{self.base_url}/auth/verify/")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Token valid for user: {result['user']['username']}")
            return result
        else:
            print(f"❌ Token verification failed: {response.text}")
            return None
    
    def logout(self):
        """Logout and blacklist refresh token"""
        if not self.refresh_token:
            print("❌ No refresh token to logout")
            return False
        
        data = {'refresh': self.refresh_token}
        response = self.session.post(f"{self.base_url}/auth/logout/", json=data)
        
        if response.status_code == 200:
            self.access_token = None
            self.refresh_token = None
            self.session.headers.pop('Authorization', None)
            print("✅ Logged out successfully")
            return True
        else:
            print(f"❌ Logout failed: {response.text}")
            return False
    
    def get_posts(self, **params):
        """Get list of posts"""
        response = self.session.get(f"{self.base_url}/posts/", params=params)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Retrieved {len(result.get('results', result))} posts")
            return result
        else:
            print(f"❌ Failed to get posts: {response.text}")
            return None
    
    def create_post(self, title, body, **extra_fields):
        """Create a new post"""
        data = {
            'title': title,
            'body': body,
            **extra_fields
        }
        
        response = self.session.post(f"{self.base_url}/posts/", json=data)
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Created post: {result['title']}")
            return result
        else:
            print(f"❌ Failed to create post: {response.text}")
            return None
    
    def get_my_profile(self):
        """Get current user's profile"""
        response = self.session.get(f"{self.base_url}/users/me/")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Profile retrieved for: {result['username']}")
            return result
        else:
            print(f"❌ Failed to get profile: {response.text}")
            return None


# Example usage and testing
def test_api():
    """Test the API with various operations"""
    client = APIClient()
    
    print("🚀 Testing API Hub Authentication")
    print("=" * 50)
    
    # Test 1: Register new user
    print("\n1. Testing User Registration...")
    user_data = client.register(
        username=f"testuser_{datetime.now().strftime('%H%M%S')}",
        email=f"test_{datetime.now().strftime('%H%M%S')}@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
        bio="I'm a test user created by the API client"
    )
    
    if not user_data:
        print("Registration failed, trying to login with existing user...")
        client.login("admin", "admin123")  # Try with superuser
    
    # Test 2: Verify token
    print("\n2. Testing Token Verification...")
    client.verify_token()
    
    # Test 3: Create a post
    print("\n3. Testing Post Creation...")
    post = client.create_post(
        title="My First API Post",
        body="This post was created using the API client with JWT authentication!",
        excerpt="Testing post creation via API"
    )
    
    # Test 4: Get posts
    print("\n4. Testing Post Retrieval...")
    posts = client.get_posts()
    
    # Test 5: Get user profile
    print("\n5. Testing Profile Retrieval...")
    profile = client.get_my_profile()
    
    # Test 6: Refresh token
    print("\n6. Testing Token Refresh...")
    client.refresh_access_token()
    
    # Test 7: Search posts
    print("\n7. Testing Post Search...")
    search_results = client.get_posts(search="API")
    
    # Test 8: Logout
    print("\n8. Testing Logout...")
    client.logout()
    
    # Test 9: Try accessing protected resource after logout
    print("\n9. Testing Access After Logout...")
    profile = client.get_my_profile()  # Should fail
    
    print("\n🎉 API Testing Complete!")


if __name__ == "__main__":
    test_api()