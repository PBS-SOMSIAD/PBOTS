"""
Authentication module for D&D RAG application using Keycloak.
"""

import os
import jwt
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from keycloak import KeycloakOpenID
import httpx

# Configuration
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "dnd-rag")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "dnd-rag-backend")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "your-client-secret")

# Initialize Keycloak
keycloak_openid = KeycloakOpenID(
    server_url=KEYCLOAK_URL,
    client_id=KEYCLOAK_CLIENT_ID,
    realm_name=KEYCLOAK_REALM,
    client_secret_key=KEYCLOAK_CLIENT_SECRET,
)

security = HTTPBearer()


class KeycloakAuth:
    def __init__(self):
        self.public_key = None
        self.token_options = {
            "verify_signature": True,
            "verify_aud": False,
            "verify_iat": True,
            "verify_exp": True,
            "verify_nbf": True,
            "verify_iss": True,
            "verify_sub": True,
            "verify_jti": True,
            "verify_at_hash": False,
            "require_aud": False,
            "require_iat": True,
            "require_exp": True,
            "require_nbf": False,
            "require_iss": True,
            "require_sub": True,
            "require_jti": True,
        }

    async def get_public_key(self) -> str:
        """Get the public key from Keycloak for token verification."""
        if self.public_key is None:
            try:
                # Get the public key from Keycloak
                self.public_key = keycloak_openid.public_key()
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Could not connect to Keycloak: {str(e)}",
                )
        return (
            f"-----BEGIN PUBLIC KEY-----\n{self.public_key}\n-----END PUBLIC KEY-----"
        )

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token."""
        try:
            public_key = await self.get_public_key()

            decoded_token = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                options=self.token_options,
                issuer=f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}",
            )

            return decoded_token

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token verification failed: {str(e)}",
            )


auth = KeycloakAuth()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """
    Dependency to get the current authenticated user.

    Usage:
        @app.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"user_id": user["sub"], "username": user["preferred_username"]}
    """
    token = credentials.credentials
    user_info = await auth.verify_token(token)
    return user_info


class UserContext:
    """Helper class to extract user information from the token."""

    def __init__(self, user_data: Dict[str, Any]):
        self.user_data = user_data

    @property
    def user_id(self) -> str:
        """Get the user ID (subject)."""
        return self.user_data.get("sub", "")

    @property
    def username(self) -> str:
        """Get the username."""
        return self.user_data.get("preferred_username", "")

    @property
    def email(self) -> str:
        """Get the user's email."""
        return self.user_data.get("email", "")

    @property
    def first_name(self) -> str:
        """Get the user's first name."""
        return self.user_data.get("given_name", "")

    @property
    def last_name(self) -> str:
        """Get the user's last name."""
        return self.user_data.get("family_name", "")

    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        return self.user_data.get("name", f"{self.first_name} {self.last_name}").strip()

    @property
    def roles(self) -> list:
        """Get the user's realm roles."""
        realm_access = self.user_data.get("realm_access", {})
        return realm_access.get("roles", [])

    def has_role(self, role: str) -> bool:
        """Check if the user has a specific role."""
        return role in self.roles


def get_user_context(user: Dict[str, Any] = Depends(get_current_user)) -> UserContext:
    """
    Dependency to get a UserContext object with convenient access to user data.

    Usage:
        @app.get("/profile")
        async def get_profile(user_context: UserContext = Depends(get_user_context)):
            return {
                "username": user_context.username,
                "full_name": user_context.full_name,
                "email": user_context.email
            }
    """
    return UserContext(user)
