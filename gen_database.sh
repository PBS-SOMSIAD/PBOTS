#!/bin/bash

# Configuration - update these values according to your Keycloak setup
KEYCLOAK_URL="http://localhost:8080"
REALM="dnd-rag"
CLIENT_ID="dnd-rag-backend"
CLIENT_SECRET=${KEYCLOAK_CLIENT_SECRET}
USERNAME="dnd_admin"
PASSWORD="dnd_admin"

# Get access token
TOKEN_RESPONSE=$(curl -s -X POST \
  "${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=${CLIENT_ID}" \
  -d "client_secret=${CLIENT_SECRET}" \
  -d "username=${USERNAME}" \
  -d "password=${PASSWORD}")

# Extract access token
ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')

if [ "$ACCESS_TOKEN" = "null" ]; then
  echo "Failed to get access token:"
  echo $TOKEN_RESPONSE
  exit 1
fi

echo "Access Token obtained successfully!"
echo "TOKEN: $ACCESS_TOKEN"

# Now call the generate database endpoint
echo "Calling generate database endpoint..."
curl -X POST http://localhost:8000/generate_database \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json"
