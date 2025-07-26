from fastapi.testclient import TestClient
from routes.document_embeddings import router
from fastapi import FastAPI

def test_document_embeddings_router_registration():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    # No endpoints to test, just ensure router can be included
    assert True 