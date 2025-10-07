import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import ChatMessage


class TestChatMessages:
    """Test suite for chat message functionality."""

    def test_create_message_success(
        self, client: TestClient, db: Session, test_user, test_project, project_token_headers
    ):
        """Test successful message creation using project token."""
        message_data = {
            "content": "Hello, this is a test message",
            "session_id": "test_session_123",
            "is_prompt_injection": False
        }

        response = client.post(
            "/api/v1/chat/messages",
            json=message_data,
            headers=project_token_headers
        )

        # The message should be in the project that the token belongs to
        # The project_token_headers uses test_project, not the auto-created default project
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == message_data["content"]
        assert data["session_id"] == message_data["session_id"]
        assert data["is_prompt_injection"] == message_data["is_prompt_injection"]
        assert data["project_id"] == test_project.id
        assert "id" in data
        assert "created_at" in data

        # Verify message was saved in database
        message = db.query(ChatMessage).filter(ChatMessage.id == data["id"]).first()
        assert message is not None
        assert message.content == message_data["content"]
        assert message.project_id == test_project.id

    def test_create_message_without_session_id(
        self, client: TestClient, db: Session, test_user, test_project, project_token_headers
    ):
        """Test message creation without session_id (should be optional)."""
        message_data = {
            "content": "Hello without session",
            "is_prompt_injection": False
        }

        response = client.post(
            "/api/v1/chat/messages",
            json=message_data,
            headers=project_token_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == message_data["content"]
        assert data["session_id"] is None
        assert data["project_id"] == test_project.id

    def test_create_message_unauthorized(self, client: TestClient):
        """Test message creation without authentication."""
        message_data = {
            "content": "Unauthorized message",
            "session_id": "test_session"
        }

        response = client.post("/api/v1/chat/messages", json=message_data)
        assert response.status_code == 401

    def test_create_message_missing_content(
        self, client: TestClient, test_user, test_project, project_token_headers
    ):
        """Test message creation with missing required content field."""
        message_data = {
            "session_id": "test_session"
        }

        response = client.post(
            "/api/v1/chat/messages",
            json=message_data,
            headers=project_token_headers
        )

        assert response.status_code == 422  # Validation error

    def test_get_messages_success(
        self, client: TestClient, db: Session, test_user, auth_headers
    ):
        """Test successful retrieval of messages."""
        # Get the user's default project (auto-created when user was created)
        from app.models import UserRole, Project
        user_role = db.query(UserRole).filter(UserRole.user_id == test_user.id).first()
        default_project = user_role.project

        # Create test messages in the default project
        messages = [
            ChatMessage(
                content=f"Test message {i}",
                session_id=f"session_{i}",
                project_id=default_project.id,
                is_prompt_injection=False
            )
            for i in range(3)
        ]

        for message in messages:
            db.add(message)
        db.commit()

        response = client.get(f"/api/v1/chat/messages?project_id={default_project.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert len(data["messages"]) == 3

        # Verify all messages belong to the correct project
        for msg in data["messages"]:
            assert msg["project_id"] == default_project.id

    def test_get_messages_with_pagination(
        self, client: TestClient, db: Session, test_project, auth_headers
    ):
        """Test message retrieval with pagination."""
        # Create 5 test messages
        messages = [
            ChatMessage(
                content=f"Test message {i}",
                session_id=f"session_{i}",
                project_id=test_project.id,
                is_prompt_injection=False
            )
            for i in range(5)
        ]

        for message in messages:
            db.add(message)
        db.commit()

        # Test with limit
        response = client.get(
            f"/api/v1/chat/messages?project_id={test_project.id}&limit=2",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 2

        # Test with skip and limit
        response = client.get(
            f"/api/v1/chat/messages?project_id={test_project.id}&skip=2&limit=2",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 2

    def test_get_messages_empty_result(
        self, client: TestClient, test_user, test_project, auth_headers
    ):
        """Test message retrieval when no messages exist."""
        response = client.get(f"/api/v1/chat/messages?project_id={test_project.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert len(data["messages"]) == 0

    def test_get_message_by_id_success(
        self, client: TestClient, db: Session, test_user, test_project, auth_headers
    ):
        """Test successful retrieval of a specific message."""
        message = ChatMessage(
            content="Specific test message",
            session_id="specific_session",
            project_id=test_project.id,
            is_prompt_injection=False
        )
        db.add(message)
        db.commit()
        db.refresh(message)

        response = client.get(
            f"/api/v1/chat/messages/{message.id}?project_id={test_project.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == message.id
        assert data["content"] == message.content
        assert data["project_id"] == test_project.id

    def test_get_message_by_id_not_found(
        self, client: TestClient, test_user, test_project, auth_headers
    ):
        """Test retrieval of non-existent message."""
        response = client.get(f"/api/v1/chat/messages/999?project_id={test_project.id}", headers=auth_headers)
        assert response.status_code == 404

    def test_project_isolation(
        self, client: TestClient, db: Session,
        test_user, test_project, auth_headers, project_token_headers,
        test_user2, test_project2, auth_headers2, project_token_headers2
    ):
        """Test that users can only see messages from their own projects."""
        # Create message in project 1 using project token
        message_data1 = {
            "content": "User 1 message",
            "session_id": "user1_session",
            "is_prompt_injection": False
        }

        response1 = client.post(
            "/api/v1/chat/messages",
            json=message_data1,
            headers=project_token_headers
        )
        assert response1.status_code == 200

        # Create message in project 2 using project token
        message_data2 = {
            "content": "User 2 message",
            "session_id": "user2_session",
            "is_prompt_injection": False
        }

        response2 = client.post(
            "/api/v1/chat/messages",
            json=message_data2,
            headers=project_token_headers2
        )
        assert response2.status_code == 200

        # User 1 should only see their message (from test_project)
        response1 = client.get(f"/api/v1/chat/messages?project_id={test_project.id}", headers=auth_headers)
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["messages"]) == 1
        assert data1["messages"][0]["content"] == "User 1 message"

        # User 2 should only see their message (from test_project2)
        response2 = client.get(f"/api/v1/chat/messages?project_id={test_project2.id}", headers=auth_headers2)
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["messages"]) == 1
        assert data2["messages"][0]["content"] == "User 2 message"

        # User 1 should not be able to access User 2's message by ID
        message2_id = data2["messages"][0]["id"]
        response = client.get(
            f"/api/v1/chat/messages/{message2_id}?project_id={test_project.id}",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_update_message_success(
        self, client: TestClient, db: Session, test_user, test_project, auth_headers
    ):
        """Test successful message update."""
        message = ChatMessage(
            content="Original message",
            session_id="update_session",
            project_id=test_project.id,
            is_prompt_injection=False
        )
        db.add(message)
        db.commit()
        db.refresh(message)

        update_data = {"is_prompt_injection": True}

        response = client.patch(
            f"/api/v1/chat/messages/{message.id}?project_id={test_project.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_prompt_injection"] is True
        assert data["content"] == "Original message"  # Content unchanged

    def test_delete_message_success(
        self, client: TestClient, db: Session, test_user, test_project, auth_headers
    ):
        """Test successful message deletion."""
        message = ChatMessage(
            content="Message to delete",
            session_id="delete_session",
            project_id=test_project.id,
            is_prompt_injection=False
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        message_id = message.id

        response = client.delete(
            f"/api/v1/chat/messages/{message_id}?project_id={test_project.id}",
            headers=auth_headers
        )

        assert response.status_code == 200

        # Verify message was deleted
        deleted_message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        assert deleted_message is None

    def test_delete_message_project_isolation(
        self, client: TestClient, db: Session,
        test_user, test_project, auth_headers,
        test_user2, test_project2
    ):
        """Test that users cannot delete messages from other projects."""
        message = ChatMessage(
            content="User 2 message",
            session_id="protected_session",
            project_id=test_project2.id,
            is_prompt_injection=False
        )
        db.add(message)
        db.commit()
        db.refresh(message)

        # User 1 tries to delete User 2's message
        response = client.delete(
            f"/api/v1/chat/messages/{message.id}?project_id={test_project2.id}",
            headers=auth_headers
        )

        assert response.status_code == 404

        # Verify message still exists
        existing_message = db.query(ChatMessage).filter(ChatMessage.id == message.id).first()
        assert existing_message is not None
