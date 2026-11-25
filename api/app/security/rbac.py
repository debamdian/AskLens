"""Role-Based Access Control (RBAC) policy loader and SQL AST enforcement."""

from pathlib import Path
from typing import Dict, List, Optional, Set
import yaml


ROLES_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "roles.yaml"


class RolePolicy:
    """Represents permissions for a single application role."""

    def __init__(
        self,
        name: str,
        description: str = "",
        allowed_tables: Optional[List[str]] = None,
        denied_columns: Optional[Dict[str, List[str]]] = None,
        mask_pii: bool = True,
        rls_region_scoped: bool = False,
    ):
        self.name = name
        self.description = description
        self.allowed_tables: Set[str] = {t.lower() for t in (allowed_tables or [])}
        self.denied_columns: Dict[str, Set[str]] = {
            tbl.lower(): {c.lower() for c in cols}
            for tbl, cols in (denied_columns or {}).items()
        }
        self.mask_pii = mask_pii
        self.rls_region_scoped = rls_region_scoped

    def is_table_allowed(self, table_name: str) -> bool:
        """Check whether the role is permitted to query the given warehouse table."""
        if "*" in self.allowed_tables:
            return True
        return table_name.lower() in self.allowed_tables

    def is_column_denied(self, table_name: Optional[str], column_name: str) -> bool:
        """Check whether a column is explicitly denied for this role."""
        col = column_name.lower()
        if table_name:
            tbl = table_name.lower()
            if tbl in self.denied_columns and col in self.denied_columns[tbl]:
                return True
        else:
            # If table qualifier is omitted, check if column is denied in any referenced table
            for denied_cols in self.denied_columns.values():
                if col in denied_cols:
                    return True
        return False


class RBACManager:
    """Loads and caches role policies from roles.yaml."""

    def __init__(self, config_path: Path = ROLES_CONFIG_PATH):
        self.config_path = config_path
        self.roles: Dict[str, RolePolicy] = {}
        self._load()

    def _load(self) -> None:
        if not self.config_path.exists():
            # Fallback default analyst policy
            self.roles["analyst"] = RolePolicy(
                name="analyst",
                allowed_tables=["regions", "customers", "products", "orders", "order_items", "returns", "marketing_spend"],
                denied_columns={"customers": ["email", "phone"]},
                mask_pii=True,
            )
            return

        with open(self.config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        for role_name, cfg in data.get("roles", {}).items():
            self.roles[role_name.lower()] = RolePolicy(
                name=role_name.lower(),
                description=cfg.get("description", ""),
                allowed_tables=cfg.get("allowed_tables", []),
                denied_columns=cfg.get("denied_columns", {}),
                mask_pii=cfg.get("mask_pii", True),
                rls_region_scoped=cfg.get("rls_region_scoped", False),
            )

    def get_policy(self, role_name: str) -> RolePolicy:
        """Return policy for role_name; defaults to strictest known role if unknown."""
        key = (role_name or "analyst").lower()
        if key in self.roles:
            return self.roles[key]
        # Fail closed to most restrictive role if unknown
        return self.roles.get("sales_manager") or next(iter(self.roles.values()))


rbac_manager = RBACManager()
