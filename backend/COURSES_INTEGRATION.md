# Courses Integration with Users Table

To test the newly modified endpoints run test_courses_endpoints.py and to add a course to a user without frontend run add_course.py

```bash
# With authentication
python test_courses_endpoints.py YOUR_AUTH_TOKEN

```

## Database Changes

### 1. Users Table Schema Update

The `users` table has been updated to include a `courses` column:

```sql
-- Add courses column as an array of course IDs
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS courses TEXT[] DEFAULT '{}';

-- Create an index for better performance when querying by courses
CREATE INDEX IF NOT EXISTS idx_users_courses ON users USING GIN (courses);
```

### 2. Database Functions

Three new database functions have been created to manage user-course relationships:

- `add_course_to_user(user_id str, course_id TEXT)` - Adds a course to a user's course list
- `remove_course_from_user(user_id str, course_id TEXT)` - Removes a course from a user's course list
- `get_user_courses(user_id str)` - Returns all courses for a user

## Backend Changes

### 1. User Models (`backend/src/user/models.py`)

Updated to include the `courses` field:

```python
class UserBase(BaseModel):
    user_id: str
    nickname: str
    email: str
    role: str
    courses: Optional[List[str]] = []
    created_at: datetime
    updated_at: datetime
```

### 2. Auth Models (`backend/src/auth/models.py`)

Updated to include the `courses` field:

```python
class AuthUser(BaseModel):
    id: str
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    role: Literal["student", "instructor", "admin"] = "student"
    courses: List[str] = []
    email_confirmed: bool = False
    created_at: Optional[datetime] = None
    last_sign_in: Optional[datetime] = None
```

### 3. User Service (`backend/src/user/service.py`)

New functions added for course management:

- `get_user_info(user_id: str)` - Get user information
- `update_user(user_id: str, user_data: UserUpdate)` - Update user information
- `add_course_to_user(user_id: str, course_id: str)` - Add course to user
- `remove_course_from_user(user_id: str, course_id: str)` - Remove course from user
- `get_user_courses(user_id: str)` - Get user's courses
- `get_users_by_course(course_id: str)` - Get users who have access to a course
- `get_all_users()` - Get all users (admin only)

### 4. User Router (`backend/src/user/router.py`)

New API endpoints:

- `GET /user/` - Get current user information
- `PUT /user/` - Update current user information
- `GET /user/courses` - Get all courses for the current user
- `POST /user/courses/{course_id}` - Add a course to the current user
- `DELETE /user/courses/{course_id}` - Remove a course from the current user
- `GET /user/all` - Get all users (admin only)
- `GET /user/by-course/{course_id}` - Get users who have access to a course (admin only)

### 5. Course Service (`backend/src/course/service.py`)

Updated to work with the new user-course relationship:

- `get_course_service(course_id: str, user_id: str)` - Get course with access validation
- `list_courses_service(user_id: str, ...)` - Get courses user has access to
- `get_course_count_service(user_id: str)` - Get course count for user
- `get_courses_by_user_service(user_id: str)` - Get all courses for a specific user

### 6. Course Router (`backend/src/course/router.py`)

Updated to use the new service functions with proper access control.

## Usage Examples

### Adding a Course to a User

```python
# Using the user service
success = service.add_course_to_user(user_id, course_id)

# Using the API endpoint
POST /user/courses/{course_id}
```

### Getting User's Courses

```python
# Using the user service
courses = service.get_user_courses(user_id)

# Using the API endpoint
GET /user/courses
```

### Getting Courses with Access Control

```python
# Using the course service
courses = service.list_courses_service(user_id)

# Using the API endpoint
GET /course/
```

## Notes

- The `courses` column is initialized as an empty array `{}` for new users
- Database functions handle duplicate prevention when adding courses
