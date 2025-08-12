#!/usr/bin/env python3
"""
Simple script to add a course to a user
Usage: python add_course.py YOUR_AUTH_TOKEN COURSE_ID [BASE_URL]
"""

import sys
import requests
import json

def add_course_to_user(token, course_id, base_url="http://localhost:8000"):
    """Add a course to the current user"""
    
    print(f"Adding course {course_id} to user...")
    print(f"Server: {base_url}")
    print()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        # First, let's get current user info
        print("1. Getting current user info...")
        response = requests.get(f"{base_url}/user/", headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            username = user_data.get('username', 'Unknown')
            current_courses = user_data.get('courses', [])
            print(f"User: {username}")
            print(f"Current courses: {len(current_courses)}")
        else:
            print(f"Failed to get user info: {response.status_code}")
            return False
        
        # Check if course already exists in user's list
        if course_id in current_courses:
            print(f"️  Course {course_id} is already in user's course list!")
            return True
        
        print()
        
        # Add the course
        print("2. Adding course to user...")
        response = requests.post(f"{base_url}/user/courses/{course_id}", headers=headers)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS: {result.get('message', 'Course added successfully')}")
            
            # Verify it was added
            print()
            print("3. Verifying course was added...")
            response = requests.get(f"{base_url}/user/courses", headers=headers)
            
            if response.status_code == 200:
                updated_courses = response.json()
                if course_id in updated_courses:
                    print(f"VERIFIED: Course {course_id} is now in user's course list")
                    print(f"Total courses: {len(updated_courses)}")
                else:
                    print(f"VERIFICATION FAILED: Course not found in user's list")
                    return False
            else:
                print(f"️  Could not verify (status: {response.status_code})")
            
            return True
            
        elif response.status_code == 404:
            print(f"FAILED: Course not found (404)")
            print(f"Make sure the course ID '{course_id}' exists")
            return False
            
        elif response.status_code == 500:
            try:
                error_data = response.json()
                detail = error_data.get('detail', 'Unknown server error')
                print(f"FAILED: Server error - {detail}")
            except:
                print(f"FAILED: Server error (500)")
            return False
            
        else:
            print(f"FAILED: Unexpected status {response.status_code}")
            try:
                print(f"Response: {response.json()}")
            except:
                print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"CONNECTION ERROR: Could not connect to {base_url}")
        print(f"Make sure the backend server is running")
        return False
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def list_available_courses(token, base_url="http://localhost:8000"):
    """List available courses"""
    
    print(f"Available courses:")
    print("-" * 40)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{base_url}/course/", headers=headers)
        
        if response.status_code == 200:
            courses = response.json()
            if courses:
                for i, course in enumerate(courses, 1):
                    print(f"{i:2}. {course.get('course_id')}")
                    print(f"{course.get('title', 'No title')}")
                    print(f"{course.get('term', 'No term')}")
                    print()
            else:
                print("   No courses available")
        else:
            print(f"Failed to get courses: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

def main():
    if len(sys.argv) < 2:
        print("Add Course to User")
        print("=" * 30)
        print()
        print("Usage:")
        print("  python add_course.py YOUR_AUTH_TOKEN COURSE_ID [BASE_URL]")
        print("  python add_course.py YOUR_AUTH_TOKEN --list [BASE_URL]")
        print()
        print("Examples:")
        print("  # Add specific course")
        print("  python add_course.py eyJhbGciOiJIUzI1... 626943e9-b0ec-4bce-b071-130fc9eb38b8")
        print()
        print("  # List available courses")
        print("  python add_course.py eyJhbGciOiJIUzI1... --list")
        print()
        print("  # Use custom server URL")
        print("  python add_course.py YOUR_TOKEN COURSE_ID http://localhost:3000")
        print()
        return
    
    token = sys.argv[1]
    
    if len(sys.argv) < 3:
        print("Missing course ID or --list flag")
        print("Usage: python add_course.py YOUR_TOKEN COURSE_ID")
        print("   or: python add_course.py YOUR_TOKEN --list")
        return
    
    course_id_or_flag = sys.argv[2]
    base_url = sys.argv[3] if len(sys.argv) > 3 else "http://localhost:8000"
    
    if course_id_or_flag == "--list":
        list_available_courses(token, base_url)
    else:
        course_id = course_id_or_flag
        success = add_course_to_user(token, course_id, base_url)
        
        if success:
            print()
            print("COMPLETED SUCCESSFULLY!")
        else:
            print()
            print("FAILED TO ADD COURSE")
            print()
            print("Troubleshooting tips:")
            print("   - Make sure the backend server is running")
            print("   - Verify your auth token is valid")
            print("   - Check that the course ID exists")
            print("   - Try listing courses with: python add_course.py YOUR_TOKEN --list")

if __name__ == "__main__":
    main()
