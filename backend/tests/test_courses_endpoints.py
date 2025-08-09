#!/usr/bin/env python3
"""
Comprehensive test script for courses integration endpoints
Tests all added and modified endpoints with detailed failure logging
"""

import requests
import json
import sys
import time
import traceback
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TestResult:
    name: str
    method: str
    endpoint: str
    status_code: int
    expected_status: int
    success: bool
    response: Any
    error: Optional[str] = None
    failure_reason: Optional[str] = None
    request_data: Optional[Dict] = None
    response_headers: Optional[Dict] = None
    execution_time: float = 0.0

class CoursesEndpointTester:
    def __init__(self, base_url: str = "http://localhost:8000", auth_token: Optional[str] = None):
        self.base_url = base_url
        self.auth_token = auth_token
        self.session = requests.Session()
        self.test_results: List[TestResult] = []
        self.created_course_id: Optional[str] = None
        self.user_id: Optional[str] = None
        self.verbose = True  # Enable detailed logging
        
        if auth_token:
            self.session.headers.update({
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            })
    
    def log_test(self, result: TestResult):
        """Log test result with detailed failure information"""
        self.test_results.append(result)
        status = "✅ PASS" if result.success else "❌ FAIL"
        
        print(f"{status} {result.method} {result.endpoint}")
        print(f"    Expected: {result.expected_status}, Got: {result.status_code}")
        print(f"    Execution Time: {result.execution_time:.2f}s")
        
        if result.success:
            # Show success details
            if result.response and isinstance(result.response, dict):
                if 'user_id' in result.response:
                    print(f"    ✅ User ID: {result.response['user_id']}")
                if 'username' in result.response:
                    print(f"    ✅ Username: {result.response['username']}")
                if 'course_id' in result.response:
                    print(f"    ✅ Course ID: {result.response['course_id']}")
                if 'courses' in result.response:
                    print(f"    ✅ Courses: {result.response['courses']}")
                if 'message' in result.response:
                    print(f"    ✅ Message: {result.response['message']}")
                if 'count' in result.response:
                    print(f"    ✅ Count: {result.response['count']}")
        else:
            # Show detailed failure information
            print(f"    FAILURE DETAILS:")
            
            if result.failure_reason:
                print(f"    Reason: {result.failure_reason}")
            
            if result.error:
                print(f"    Error: {result.error}")
            
            # Show request details
            if result.request_data:
                print(f"    Request Data: {json.dumps(result.request_data, indent=6)}")
            
            # Show response details
            if result.response:
                print(f"    Response Body:")
                if isinstance(result.response, dict):
                    print(f"        {json.dumps(result.response, indent=8)}")
                else:
                    print(f"        {str(result.response)[:500]}")
            
            # Show response headers for debugging
            if result.response_headers:
                print(f"    Response Headers:")
                for key, value in result.response_headers.items():
                    if key.lower() in ['content-type', 'content-length', 'server', 'date']:
                        print(f"        {key}: {value}")
            
        
        print()
    
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                    expected_status: int = 200, description: str = "") -> TestResult:
        """Make HTTP request and return detailed test result"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        print(f"🔄 Testing: {method} {endpoint}")
        if description:
            print(f"    {description}")
        
        try:
            # Make the request
            if method.upper() == "GET":
                response = self.session.get(url, timeout=30)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, timeout=30)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, timeout=30)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            execution_time = time.time() - start_time
            success = response.status_code == expected_status
            
            # Parse response
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = response.text if response.text else None
            
            # Determine failure reason if not successful
            failure_reason = None
            if not success:
                if response.status_code != expected_status:
                    failure_reason = f"Expected HTTP {expected_status}, got HTTP {response.status_code}"
                
                # Add specific failure context
                if response.status_code == 401:
                    failure_reason += " - Authentication required or token invalid"
                elif response.status_code == 403:
                    failure_reason += " - Access forbidden"
                elif response.status_code == 404:
                    failure_reason += " - Resource not found"
                elif response.status_code >= 500:
                    failure_reason += " - Server error"
            
            return TestResult(
                name=f"{method} {endpoint}",
                method=method,
                endpoint=endpoint,
                status_code=response.status_code,
                expected_status=expected_status,
                success=success,
                response=response_data,
                failure_reason=failure_reason,
                request_data=data,
                response_headers=dict(response.headers),
                execution_time=execution_time
            )
            
        except requests.exceptions.ConnectionError as e:
            execution_time = time.time() - start_time
            return TestResult(
                name=f"{method} {endpoint}",
                method=method,
                endpoint=endpoint,
                status_code=0,
                expected_status=expected_status,
                success=False,
                response=None,
                error=f"Connection failed: {str(e)}",
                failure_reason="Cannot connect to server - server may not be running",
                request_data=data,
                execution_time=execution_time
            )
        
        except requests.exceptions.Timeout as e:
            execution_time = time.time() - start_time
            return TestResult(
                name=f"{method} {endpoint}",
                method=method,
                endpoint=endpoint,
                status_code=0,
                expected_status=expected_status,
                success=False,
                response=None,
                error=f"Request timeout: {str(e)}",
                failure_reason="Request took too long - server may be overloaded",
                request_data=data,
                execution_time=execution_time
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                name=f"{method} {endpoint}",
                method=method,
                endpoint=endpoint,
                status_code=0,
                expected_status=expected_status,
                success=False,
                response=None,
                error=f"Unexpected error: {str(e)}",
                failure_reason=f"Exception occurred: {type(e).__name__}",
                request_data=data,
                execution_time=execution_time
            )
    
    def test_health_check(self):
        """Test server health with detailed logging"""
        print("HEALTH CHECK")
        print("-" * 60)
        
        result = self.make_request("GET", "/docs", description="Check if server is running")
        self.log_test(result)
        
        if not result.success:
            print("CRITICAL: Server is not accessible!")
            print("   This will cause all subsequent tests to fail.")
            print("   Please ensure your backend server is running:")
            print("   cd WatAIOliver/backend && python -m src.main")
            return False
        
        # Additional health checks
        print("Additional server checks...")
        
        # Check if auth endpoints exist
        result = self.make_request("GET", "/", description="Check root endpoint")
        if result.status_code == 404:
            print("   Root endpoint not found (normal)")
        
        return True
    
    def test_user_endpoints(self):
        """Test all user-related endpoints with detailed logging"""
        print("USER ENDPOINTS")
        print("-" * 60)
        
        # 1. Get current user info
        result = self.make_request("GET", "/user/", description="Get current user information")
        self.log_test(result)
        
        if result.success and result.response:
            self.user_id = result.response.get("user_id")
            print(f"Captured User ID: {self.user_id}")
            
            # Validate user data structure
            required_fields = ['user_id', 'email', 'role']
            missing_fields = [field for field in required_fields if field not in result.response]
            if missing_fields:
                print(f"    Missing expected fields: {missing_fields}")
        else:
            print("    Cannot proceed with user tests - authentication failed")
            if not self.auth_token:
                print("    No auth token provided - this is expected to fail")
            return
        
        # 2. Update user info
        update_data = {"username": "Test User Updated"}
        result = self.make_request("PUT", "/user/", update_data, 
                                 description="Update user information")
        self.log_test(result)
        
        # 3. Get user courses (should be empty initially)
        result = self.make_request("GET", "/user/courses", 
                                 description="Get user's courses (should be empty initially)")
        self.log_test(result)
        
        if result.success:
            courses = result.response if isinstance(result.response, list) else []
            print(f"    User currently has {len(courses)} courses")
        
        # 4. Try to get all users (admin endpoint - may fail if not admin)
        result = self.make_request("GET", "/user/all", expected_status=200,
                                 description="Get all users (admin only)")
        if result.status_code == 403:
            result.expected_status = 403
            result.success = True
            result.failure_reason = None
            print("    Admin access required (expected for non-admin users)")
        self.log_test(result)
    
    def test_course_endpoints(self):
        """Test all course-related endpoints with detailed logging"""
        print("COURSE ENDPOINTS")
        print("-" * 60)
        
        # 1. List courses (may be empty if user has no courses)
        result = self.make_request("GET", "/course/", 
                                 description="List courses user has access to")
        self.log_test(result)
        
        if result.success:
            courses = result.response if isinstance(result.response, list) else []
            print(f"    User has access to {len(courses)} courses")
        
        # 2. Create a test course
        course_data = {
            "title": "Test Course for API Testing",
            "description": "A test course created by the endpoint tester",
            "term": "Test Term 2024"
        }
        result = self.make_request("POST", "/course/", course_data, expected_status=201,
                                 description="Create a new test course")
        self.log_test(result)
        
        if result.success and result.response:
            self.created_course_id = result.response.get("course_id")
            print(f"Created Course ID: {self.created_course_id}")
            
            # Validate course data structure
            expected_fields = ['course_id', 'title', 'created_by']
            missing_fields = [field for field in expected_fields if field not in result.response]
            if missing_fields:
                print(f"    Missing expected fields in course: {missing_fields}")
        else:
            print("    Course creation failed - subsequent course tests may fail")
        
        # 3. Get course count
        result = self.make_request("GET", "/course/count/total",
                                 description="Get user's course count")
        self.log_test(result)
        
        # 4. Get specific course (if we created one)
        if self.created_course_id:
            result = self.make_request("GET", f"/course/{self.created_course_id}",
                                     description=f"Get specific course: {self.created_course_id}")
            self.log_test(result)
        else:
            print("    Skipping course retrieval - no test course created")
        
        # 5. Update course (if we created one)
        if self.created_course_id:
            update_data = {"description": "Updated description for test course"}
            result = self.make_request("PUT", f"/course/{self.created_course_id}", update_data,
                                     description="Update test course")
            self.log_test(result)
        else:
            print("    Skipping course update - no test course created")
    
    def test_user_course_integration(self):
        """Test user-course relationship endpoints with detailed logging"""
        print("USER-COURSE INTEGRATION")
        print("-" * 60)
        
        if not self.created_course_id:
            print("No test course available, skipping integration tests")
            print("   This means course creation failed in previous step")
            return
        
        print(f"Testing integration with course: {self.created_course_id}")
        
        # 1. Add course to user
        result = self.make_request("POST", f"/user/courses/{self.created_course_id}",
                                 description="Add course to current user")
        self.log_test(result)
        
        # 2. Verify course was added to user
        result = self.make_request("GET", "/user/courses",
                                 description="Verify course was added to user")
        self.log_test(result)
        
        if result.success and result.response:
            courses = result.response if isinstance(result.response, list) else []
            if self.created_course_id in courses:
                print("    ✅ Course successfully added to user")
            else:
                print("    ❌ Course not found in user's courses after addition")
                print(f"    🔍 Expected: {self.created_course_id}")
                print(f"    🔍 Found: {courses}")
        
        # 3. Get user info to see courses in profile
        result = self.make_request("GET", "/user/",
                                 description="Check if course appears in user profile")
        self.log_test(result)
        
        # 4. List courses again (should now show the course)
        result = self.make_request("GET", "/course/",
                                 description="Verify course appears in accessible courses")
        self.log_test(result)
        
        # 5. Test access to course (should work now)
        result = self.make_request("GET", f"/course/{self.created_course_id}",
                                 description="Test access to course after adding to user")
        self.log_test(result)
        
        # 6. Remove course from user
        result = self.make_request("DELETE", f"/user/courses/{self.created_course_id}",
                                 description="Remove course from user")
        self.log_test(result)
        
        # 7. Verify course was removed
        result = self.make_request("GET", "/user/courses",
                                 description="Verify course was removed from user")
        self.log_test(result)
        
        if result.success and result.response:
            courses = result.response if isinstance(result.response, list) else []
            if self.created_course_id not in courses:
                print("    ✅ Course successfully removed from user")
            else:
                print("    ❌ Course still found in user's courses after removal")
                print(f"    🔍 Unexpected: {self.created_course_id}")
                print(f"    🔍 Found: {courses}")
        
        # 8. Test access after removal (creators still have access)
        result = self.make_request("GET", f"/course/{self.created_course_id}", expected_status=200,
                                 description="Test creator access after course removal (creators keep access)")
        if result.success:
            print("    Course creator retains access even after removing from courses list")
        self.log_test(result)
    
    def test_admin_endpoints(self):
        """Test admin-only endpoints with detailed logging"""
        print("ADMIN ENDPOINTS")
        print("-" * 60)
        
        # 1. Get users by course (admin only)
        if self.created_course_id:
            result = self.make_request("GET", f"/user/by-course/{self.created_course_id}",
                                     description="Get users who have access to course (admin only)")
            if result.status_code == 403:
                result.expected_status = 403
                result.success = True
                result.failure_reason = None
                print("    Admin access required (expected for non-admin users)")
            self.log_test(result)
        else:
            print("    Skipping admin course test - no test course available")
    
    def test_error_cases(self):
        """Test error handling with detailed logging"""
        print("ERROR HANDLING")
        print("-" * 60)
        
        # 1. Try to get non-existent course
        result = self.make_request("GET", "/course/non-existent-course", expected_status=500,
                                 description="Test 500 error for non-existent course")
        self.log_test(result)
        
        # 2. Try to add non-existent course to user
        result = self.make_request("POST", "/user/courses/non-existent-course", expected_status=500,
                                 description="Test error when adding non-existent course")
        # Accept either 404 or 500 as valid error responses
        if result.status_code in [404, 500]:
            result.expected_status = result.status_code
            result.success = True
            result.failure_reason = None
        self.log_test(result)
        
        # 3. Try to remove non-existent course from user
        result = self.make_request("DELETE", "/user/courses/non-existent-course",
                                 description="Test removing non-existent course from user")
        # This might succeed (no-op) or fail, both are acceptable
        if result.status_code in [200, 404, 500]:
            result.expected_status = result.status_code
            result.success = True
            result.failure_reason = None
        self.log_test(result)
        
        # 4. Test malformed requests
        result = self.make_request("POST", "/course/", {"invalid": "data"}, expected_status=422,
                                 description="Test validation error with malformed course data")
        # Accept various error codes for validation failures
        if result.status_code in [400, 422, 500]:
            result.expected_status = result.status_code
            result.success = True
            result.failure_reason = None
        self.log_test(result)
        
        # 5. Test access control for courses user doesn't have access to
        # Create a fake course ID that the user definitely doesn't have access to
        fake_course_id = "fake-course-id-for-access-test"
        result = self.make_request("GET", f"/course/{fake_course_id}", expected_status=500,
                                 description="Test access to non-existent course (should be 500)")
        # This should be 500 (not found) rather than 403 (access denied) for non-existent courses
        self.log_test(result)
    
    def cleanup(self):
        """Clean up test data with detailed logging"""
        print("CLEANUP")
        print("-" * 60)
        
        # Delete test course if created
        if self.created_course_id:
            result = self.make_request("DELETE", f"/course/{self.created_course_id}", 
                                     expected_status=204,
                                     description=f"Delete test course: {self.created_course_id}")
            # Accept 200 or 204 as success for deletion
            if result.status_code in [200, 204]:
                result.expected_status = result.status_code
                result.success = True
                result.failure_reason = None
            self.log_test(result)
        else:
            print("    No test course to clean up")
    
    def run_all_tests(self):
        """Run all tests with comprehensive logging"""
        start_time = datetime.now()
        
        print("COURSES INTEGRATION ENDPOINT TESTING")
        print("=" * 80)
        print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Base URL: {self.base_url}")
        print(f"Auth Token: {'✅ Provided' if self.auth_token else '❌ Not provided'}")
        if self.auth_token:
            print(f"Token Preview: {self.auth_token[:30]}...")
        print()
        
        if not self.auth_token:
            print("WARNING: No auth token provided!")
            print("   Most tests will fail with 401 Unauthorized")
            print("   Usage: python test_courses_endpoints.py YOUR_AUTH_TOKEN")
            print("   Get token from: localStorage.getItem('access_token') in browser")
            print()
        
        # Run test suites
        try:
            if not self.test_health_check():
                print("ABORTING: Server health check failed")
                return
            
            self.test_user_endpoints()
            self.test_course_endpoints()
            self.test_user_course_integration()
            self.test_admin_endpoints()
            self.test_error_cases()
            self.cleanup()
            
        except KeyboardInterrupt:
            print("\n Tests interrupted by user")
        except Exception as e:
            print(f"\n Unexpected error during testing: {e}")
            traceback.print_exc()
        
        # Summary
        end_time = datetime.now()
        self.print_summary(start_time, end_time)
    
    def print_summary(self, start_time: datetime, end_time: datetime):
        """Print comprehensive test summary"""
        duration = end_time - start_time
        
        print("DETAILED TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.success)
        failed_tests = total_tests - passed_tests
        
        print(f"⏱️  Duration: {duration.total_seconds():.2f} seconds")
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS SUMMARY:")
            print("-" * 40)
            for i, result in enumerate([r for r in self.test_results if not r.success], 1):
                print(f"{i}. {result.name}")
                print(f"   Status: {result.status_code} (expected {result.expected_status})")
                if result.failure_reason:
                    print(f"   Reason: {result.failure_reason}")
                if result.error:
                    print(f"   Error: {result.error}")
                print()
        
        print(f"\nENDPOINTS TESTED:")
        print("-" * 40)
        endpoints = {}
        for result in self.test_results:
            key = f"{result.method} {result.endpoint}"
            if key not in endpoints:
                endpoints[key] = {'passed': 0, 'failed': 0}
            if result.success:
                endpoints[key]['passed'] += 1
            else:
                endpoints[key]['failed'] += 1
        
        for endpoint, stats in sorted(endpoints.items()):
            status = "✅" if stats['failed'] == 0 else "❌"
            print(f"  {status} {endpoint} (P:{stats['passed']} F:{stats['failed']})")
        
        # Performance summary
        if self.test_results:
            avg_time = sum(r.execution_time for r in self.test_results) / len(self.test_results)
            max_time = max(r.execution_time for r in self.test_results)
            print(f"\nPERFORMANCE:")
            print(f"   Average response time: {avg_time:.2f}s")
            print(f"   Slowest response time: {max_time:.2f}s")
        
        # Final verdict
        print(f"\n{'ALL TESTS PASSED!' if failed_tests == 0 else 'SOME TESTS FAILED'}")
        

def main():
    """Main function with argument handling"""
    auth_token = sys.argv[1] if len(sys.argv) > 1 else None
    base_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000"
    
    print("Configuration:")
    print(f"   Base URL: {base_url}")
    print(f"   Auth Token: {'Provided' if auth_token else 'Not provided'}")
    print()
    
    tester = CoursesEndpointTester(base_url=base_url, auth_token=auth_token)
    tester.run_all_tests()

if __name__ == "__main__":
    main()