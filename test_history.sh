#!/bin/bash

API_URL="http://127.0.0.1:8000"
BASE_URL="http://localhost:3001"

echo "=== Testing Chat History Flow ==="
echo ""

# Step 1: Register user
echo "1. Registering user..."
REGISTER=$(curl -s -X POST "$API_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "history_test@example.com",
    "password": "Test123!@#",
    "full_name": "History Tester"
  }' \
  -c cookies.txt)

echo "Response: $REGISTER"
USER_ID=$(echo $REGISTER | jq -r '.user.id // .id // "unknown"')
echo "User ID: $USER_ID"
echo ""

# Step 2: Get user info to verify auth
echo "2. Verifying authentication..."
curl -s -X GET "$API_URL/api/v1/auth/me" \
  -H "Content-Type: application/json" \
  -b cookies.txt | jq '.'
echo ""

# Step 3: Get documents list
echo "3. Getting documents list..."
curl -s -X GET "$API_URL/api/v1/rag/documents" \
  -b cookies.txt | jq '.'
echo ""

# Step 4: Get chat sessions list
echo "4. Getting chat sessions list..."
curl -s -X GET "$API_URL/api/v1/rag/chat/sessions" \
  -b cookies.txt | jq '.'
echo ""

# Step 5: Send first chat message
echo "5. Sending first chat message..."
SESSION_ID="session_test_$(date +%s)"
CHAT_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/rag/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Hello, how are you?\",
    \"session_id\": \"$SESSION_ID\"
  }" \
  -b cookies.txt)

echo "Response: $CHAT_RESPONSE"
echo ""

# Step 6: Send second chat message
echo "6. Sending second chat message..."
curl -s -X POST "$API_URL/api/v1/rag/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"What is RAG?\",
    \"session_id\": \"$SESSION_ID\"
  }" \
  -b cookies.txt | jq '.'
echo ""

# Step 7: Load chat history
echo "7. Loading chat history for session: $SESSION_ID"
curl -s -X GET "$API_URL/api/v1/rag/chat/history/$SESSION_ID" \
  -b cookies.txt | jq '.'
echo ""

# Step 8: Get updated sessions list
echo "8. Getting updated chat sessions list..."
curl -s -X GET "$API_URL/api/v1/rag/chat/sessions" \
  -b cookies.txt | jq '.'
echo ""

echo "=== Test Complete ==="
