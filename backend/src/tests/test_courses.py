import pytest
from fastapi.testclient import TestClient
from routes.courses import router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)

client = TestClient(app)

@pytest.fixture
def course_data():
    return {"title": "Test Course", "description": "A test course."}

def test_create_course(course_data):
    response = client.post("/course/", json=course_data)
    assert response.status_code in (200, 201)
    assert "course_id" in response.json() or response.json().get("title") == course_data["title"]

def test_get_courses():
    user_id = "testuser"
    response = client.get(f"/course/{user_id}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_update_course(course_data):
    course_id = "testcourseid"
    response = client.put(f"/course/{course_id}", json=course_data)
    assert response.status_code == 200
    assert response.json().get("title") == course_data["title"]

def test_delete_course():
    course_id = "testcourseid"
    response = client.delete(f"/course/{course_id}")
    assert response.status_code in (200, 204) 