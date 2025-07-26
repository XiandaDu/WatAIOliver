from fastapi.testclient import TestClient
from routes.users import router
from fastapi import FastAPI

def test_users_router_registration():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    # No endpoints to test, just ensure router can be included
    assert True 