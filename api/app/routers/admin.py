"""Admin Router for Audit Logs, Golden Queries, and RBAC Role Inspection."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query
from app.security.audit import audit_logger
from app.security.rbac import rbac_manager
from app.schema.retriever import schema_retriever

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@router.get("/audit-logs")
def list_audit_logs(limit: int = Query(50, ge=1, le=200)) -> Dict[str, Any]:
    """Return recent query audit logs."""
    logs = audit_logger.get_recent_logs(limit=limit)
    return {"logs": logs, "count": len(logs)}


@router.get("/golden-queries")
def list_golden_queries() -> Dict[str, Any]:
    """Return all golden question -> SQL pairs."""
    return {
        "golden_queries": schema_retriever.golden_queries,
        "count": len(schema_retriever.golden_queries),
    }


@router.get("/roles")
def list_roles() -> Dict[str, Any]:
    """Return configured RBAC roles and table/column policies."""
    roles_out: List[Dict[str, Any]] = []
    for name, policy in rbac_manager.roles.items():
        roles_out.append(
            {
                "name": name,
                "description": policy.description,
                "allowed_tables": sorted(policy.allowed_tables),
                "denied_columns": {k: sorted(v) for k, v in policy.denied_columns.items()},
                "mask_pii": policy.mask_pii,
                "rls_region_scoped": policy.rls_region_scoped,
            }
        )
    return {"roles": roles_out}
