import sys
from unittest.mock import MagicMock
import uuid
from datetime import datetime, timezone

# Create a mock that returns realistic data
def create_realistic_mock_response(data_type="course"):
    if data_type == "course":
        return {
            "course_id": str(uuid.uuid4()),
            "title": "Test Course",
            "description": "A test course description",
            "term": "Fall 2024",
            "created_by": "testuser",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    elif data_type == "conversation":
        return {
            "conversation_id": str(uuid.uuid4()),
            "title": "Test Conversation",
            "user_id": "testuser",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    elif data_type == "course_model":
        return {
            "course_id": str(uuid.uuid4()),
            "model_id": "testmodel"
        }
    else:
        return {"id": str(uuid.uuid4())}

# Create a mock Supabase client
mock_supabase = MagicMock()

# Table name tracking
table_name_holder = {"name": "course"}

def table_side_effect(name):
    table_name_holder["name"] = name
    return mock_table

mock_supabase.table.side_effect = table_side_effect

# Mock the table methods
mock_table = MagicMock()
mock_insert = MagicMock()
mock_update = MagicMock()
mock_delete = MagicMock()
mock_select = MagicMock()
mock_table.insert.return_value = mock_insert
mock_table.update.return_value = mock_update
mock_table.delete.return_value = mock_delete
mock_table.select.return_value = mock_select
mock_insert.eq.return_value = mock_insert
mock_update.eq.return_value = mock_update
mock_delete.eq.return_value = mock_delete
mock_select.eq.return_value = mock_select

class MockResponse:
    def __init__(self, data):
        self.data = data

def mock_execute(*args, **kwargs):
    table = table_name_holder["name"]
    if table == "courses":
        return MockResponse([create_realistic_mock_response("course")])
    elif table == "conversations":
        return MockResponse([create_realistic_mock_response("conversation")])
    elif table == "course_models":
        return MockResponse([create_realistic_mock_response("course_model")])
    else:
        return MockResponse([create_realistic_mock_response()])

mock_insert.execute = mock_execute
mock_update.execute = mock_execute
mock_delete.execute = mock_execute
mock_select.execute = mock_execute

# Mock the db.client module
sys.modules["db.client"] = MagicMock()
sys.modules["db.client"].supabase = mock_supabase 