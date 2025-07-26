from fastapi.testclient import TestClient
from routes.messages import router
from fastapi import FastAPI

def test_messages_router_registration():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    # No endpoints to test, just ensure router can be included
    assert True 