"""API authentication via bearer token (API key)."""

import hashlib
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage comparison."""
    return hashlib.sha256(api_key.encode()).hexdigest()


async def verify_api_key(
    credentials: Annotated[HTTPAuthorizationCredentials, Security(security)],
) -> dict:
    """Verify the bearer token against stored API key hashes.

    For POC, uses a simple in-memory check.
    Production should query the tenants table.
    """
    token = credentials.credentials
    key_hash = hash_api_key(token)

    # POC: check against environment or in-memory tenant registry
    # In production, this queries the tenants table
    from landscraper.api.tenant_registry import get_tenant_by_key_hash

    tenant = get_tenant_by_key_hash(key_hash)
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    if not tenant.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant account is inactive",
        )

    return tenant
