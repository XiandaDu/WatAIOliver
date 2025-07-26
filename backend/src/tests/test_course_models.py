import pytest
from fastapi.testclient import TestClient
from routes.course_models import router
from fastapi import FastAPI
import json

app = FastAPI()
app.include_router(router)

client = TestClient(app)

@pytest.fixture
def course_model_data():
    return {"course_id": "testcourse", "model_id": "testmodel"}

def test_create_course_model(course_model_data):
    response = client.post("/course-models/", json=course_model_data)
    assert response.status_code in (200, 201)
    assert "course_id" in response.json() or response.json().get("model_id") == course_model_data["model_id"]

def test_get_course_models():
    course_id = "testcourse"
    response = client.get(f"/course-models/{course_id}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_delete_course_model(course_model_data):
    response = client.request(
        "DELETE",
        "/course-models/",
        json=course_model_data
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list) 