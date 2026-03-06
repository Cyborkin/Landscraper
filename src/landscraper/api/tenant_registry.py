"""In-memory tenant registry for POC.

Production: replace with database queries against the tenants table.
"""

from landscraper.api.auth import hash_api_key

# POC tenant registry — populated at startup or via env vars
_TENANTS: dict[str, dict] = {}


def register_tenant(name: str, api_key: str, tenant_id: str = "default") -> None:
    """Register a tenant with their API key."""
    key_hash = hash_api_key(api_key)
    _TENANTS[key_hash] = {
        "id": tenant_id,
        "name": name,
        "is_active": True,
        "api_key_hash": key_hash,
    }


def get_tenant_by_key_hash(key_hash: str) -> dict | None:
    """Look up a tenant by their API key hash."""
    return _TENANTS.get(key_hash)


def register_default_tenant() -> None:
    """Register a default POC tenant if none exist."""
    if not _TENANTS:
        register_tenant(
            name="POC Tenant",
            api_key="landscraper-poc-key",
            tenant_id="poc-tenant-001",
        )
