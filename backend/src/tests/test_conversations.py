import pytest
from fastapi.testclient import TestClient
from routes.conversations import router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)

client = TestClient(app)

@pytest.fixture
def conversation_data():
    return {"conversation_id": "testconv", "title": "Test Conversation", "user_id": "testuser"}

def test_create_conversation(conversation_data):
    response = client.post("/conversations/", json=conversation_data)
    assert response.status_code in (200, 201)
    assert "conversation_id" in response.json() or response.json().get("title") == conversation_data["title"]

def test_get_conversations():
    user_id = "testuser"
    response = client.get(f"/conversations/{user_id}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_update_conversation():
    conversation_id = "testconv"
    update_data = {"title": "Updated Title"}
    response = client.put(f"/conversations/{conversation_id}", json=update_data)
    assert response.status_code == 200
    assert any(["title" in conv for conv in response.json()])

def test_delete_conversation():
    conversation_id = "testconv"
    response = client.delete(f"/conversations/{conversation_id}")
    assert response.status_code == 200
    assert isinstance(response.json(), list) 