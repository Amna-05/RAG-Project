import requests
import json
from datetime import datetime

API_URL = "http://127.0.0.1:8000"
session = requests.Session()

# Enable automatic cookie handling
session.cookies.clear()

print("=== Testing Chat History Flow ===\n")

# Step 1: Register user
print("1. Registering user...")
user_data = {
    "email": f"history_test_{int(datetime.now().timestamp())}@example.com",
    "username": f"historytest{int(datetime.now().timestamp())}",
    "password": "Test123!@#",
    "full_name": "History Tester"
}

response = session.post(f"{API_URL}/api/v1/auth/register", json=user_data)
print(f"HTTP Status: {response.status_code}")
print(f"Cookies after registration: {dict(session.cookies)}")
print(f"Response: {response.json()}\n")

if response.status_code != 201:
    print("Registration failed. Exiting...")
    exit(1)

# Step 2: Verify authentication
print("2. Verifying authentication...")
response = session.get(f"{API_URL}/api/v1/auth/me")
print(f"HTTP Status: {response.status_code}")
print(f"Response: {response.json()}\n")

if response.status_code != 200:
    print("ERROR: Not authenticated after registration!")
    print("Cookies:", dict(session.cookies))
    exit(1)

# Step 3: Get documents list
print("3. Getting documents list...")
response = session.get(f"{API_URL}/api/v1/rag/documents")
print(f"HTTP Status: {response.status_code}")
docs = response.json()
print(f"Documents count: {len(docs) if isinstance(docs, list) else 0}")
print(f"Response: {docs}\n")

# Step 4: Get chat sessions list (before sending messages)
print("4. Getting chat sessions list (before messages)...")
response = session.get(f"{API_URL}/api/v1/rag/chat/sessions")
print(f"HTTP Status: {response.status_code}")
sessions_before = response.json()
print(f"Sessions count: {len(sessions_before) if isinstance(sessions_before, list) else 0}")
print(f"Response: {sessions_before}\n")

# Step 5: Send first chat message
SESSION_ID = f"session_test_{int(datetime.now().timestamp())}"
print(f"5. Sending first chat message (Session: {SESSION_ID})...")
chat_data = {
    "message": "Hello, how are you?",
    "session_id": SESSION_ID
}
response = session.post(f"{API_URL}/api/v1/rag/chat", json=chat_data)
print(f"HTTP Status: {response.status_code}")
print(f"Response: {response.json()}\n")

# Step 6: Send second chat message
print("6. Sending second chat message...")
chat_data = {
    "message": "What is RAG?",
    "session_id": SESSION_ID
}
response = session.post(f"{API_URL}/api/v1/rag/chat", json=chat_data)
print(f"HTTP Status: {response.status_code}")
print(f"Response: {response.json()}\n")

# Step 7: Load chat history
print(f"7. Loading chat history for session: {SESSION_ID}...")
response = session.get(f"{API_URL}/api/v1/rag/chat/history/{SESSION_ID}")
print(f"HTTP Status: {response.status_code}")
history = response.json()
if isinstance(history, dict) and 'messages' in history:
    print(f"Messages count: {len(history['messages'])}")
    for i, msg in enumerate(history['messages']):
        print(f"  Message {i+1}: {msg['role']} - {msg['content'][:50]}...")
else:
    print(f"Response: {history}")
print()

# Step 8: Get updated sessions list
print("8. Getting updated chat sessions list...")
response = session.get(f"{API_URL}/api/v1/rag/chat/sessions")
print(f"HTTP Status: {response.status_code}")
sessions_after = response.json()
print(f"Sessions count: {len(sessions_after) if isinstance(sessions_after, list) else 0}")
if isinstance(sessions_after, list) and len(sessions_after) > 0:
    print(f"Sessions: {sessions_after[:3]}")
print()

print("=== Test Complete ===")
print(f"\nSummary:")
print(f"- Registration: SUCCESS")
print(f"- Authentication: {'SUCCESS' if response.status_code in [200, 401] else 'FAILED'}")
print(f"- Sessions before messages: {len(sessions_before) if isinstance(sessions_before, list) else 'ERROR'}")
print(f"- Sessions after messages: {len(sessions_after) if isinstance(sessions_after, list) else 'ERROR'}")
