"""Schema Crawler for PostgreSQL Warehouse.

Extracts table names, columns, data types, primary/foreign keys, row counts,
and sample values from information_schema and pg_catalog.
"""

from typing import Any, Dict, List
import psycopg2
from psycopg2.extras import RealDictCursor
from app.core.config import settings


class SchemaCrawler:
    """Introspects the target database schema."""

    def __init__(self, connection_url: str = None, target_schema: str = "warehouse"):
        self.connection_url = connection_url or settings.sync_admin_url
        self.target_schema = target_schema
        self._cached_schema: Dict[str, Any] = {}

    def crawl(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Crawls schema metadata and returns a structured dictionary."""
        if self._cached_schema and not force_refresh:
            return self._cached_schema

        schema_info: Dict[str, Any] = {
            "schema_name": self.target_schema,
            "tables": {}
        }

        with psycopg2.connect(self.connection_url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 1. Fetch tables
                cur.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = %s AND table_type = 'BASE TABLE'
                    ORDER BY table_name;
                """, (self.target_schema,))
                tables = [r["table_name"] for r in cur.fetchall()]

                for tbl in tables:
                    # 2. Fetch columns and data types
                    cur.execute("""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns
                        WHERE table_schema = %s AND table_name = %s
                        ORDER BY ordinal_position;
                    """, (self.target_schema, tbl))
                    columns = cur.fetchall()

                    # 3. Fetch Primary Keys
                    cur.execute("""
                        SELECT kcu.column_name
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu
                          ON tc.constraint_name = kcu.constraint_name
                          AND tc.table_schema = kcu.table_schema
                        WHERE tc.constraint_type = 'PRIMARY KEY'
                          AND tc.table_schema = %s
                          AND tc.table_name = %s;
                    """, (self.target_schema, tbl))
                    pks = [r["column_name"] for r in cur.fetchall()]

                    # 4. Fetch Foreign Keys
                    cur.execute("""
                        SELECT
                            kcu.column_name,
                            ccu.table_name AS foreign_table_name,
                            ccu.column_name AS foreign_column_name
                        FROM information_schema.table_constraints AS tc
                        JOIN information_schema.key_column_usage AS kcu
                          ON tc.constraint_name = kcu.constraint_name
                          AND tc.table_schema = kcu.table_schema
                        JOIN information_schema.constraint_column_usage AS ccu
                          ON ccu.constraint_name = tc.constraint_name
                          AND ccu.table_schema = tc.table_schema
                        WHERE tc.constraint_type = 'FOREIGN KEY'
                          AND tc.table_schema = %s
                          AND tc.table_name = %s;
                    """, (self.target_schema, tbl))
                    fks = {r["column_name"]: f"{r['foreign_table_name']}.{r['foreign_column_name']}" for r in cur.fetchall()}

                    # 5. Row count estimation
                    cur.execute(f"SELECT COUNT(*) AS cnt FROM {self.target_schema}.{tbl};")
                    row_count = cur.fetchone()["cnt"]

                    # 6. Sample values for low-cardinality/interesting columns
                    col_samples = {}
                    for col in columns:
                        c_name = col["column_name"]
                        c_type = col["data_type"]
                        # Skip password, keys, large blobs
                        if "password" in c_name or c_type in ["bytea", "text"] and c_name.endswith("_id"):
                            continue
                        try:
                            cur.execute(f"""
                                SELECT DISTINCT {c_name}
                                FROM {self.target_schema}.{tbl}
                                WHERE {c_name} IS NOT NULL
                                LIMIT 4;
                            """)
                            samples = [str(r[c_name]) for r in cur.fetchall()]
                            if samples:
                                col_samples[c_name] = samples
                        except Exception:
                            pass

                    schema_info["tables"][tbl] = {
                        "row_count": row_count,
                        "primary_keys": pks,
                        "foreign_keys": fks,
                        "columns": [
                            {
                                "name": c["column_name"],
                                "type": c["data_type"],
                                "nullable": c["is_nullable"] == "YES",
                                "sample_values": col_samples.get(c["column_name"], [])
                            }
                            for c in columns
                        ]
                    }

        self._cached_schema = schema_info
        return schema_info

    def get_prompt_formatted_schema(self, table_whitelist: List[str] = None) -> str:
        """Formats the crawled schema into a compact, human-readable prompt string."""
        data = self.crawl()
        lines = [f"Database Schema: '{self.target_schema}'\n"]

        for tbl, details in data["tables"].items():
            if table_whitelist and tbl not in table_whitelist:
                continue

            lines.append(f"Table: {self.target_schema}.{tbl} (Rows: ~{details['row_count']})")
            if details["primary_keys"]:
                lines.append(f"  Primary Key: {', '.join(details['primary_keys'])}")
            if details["foreign_keys"]:
                fk_strs = [f"{col} -> {target}" for col, target in details["foreign_keys"].items()]
                lines.append(f"  Foreign Keys: {', '.join(fk_strs)}")

            lines.append("  Columns:")
            for col in details["columns"]:
                samples_str = f" [e.g. {', '.join(repr(s) for s in col['sample_values'][:3])}]" if col["sample_values"] else ""
                lines.append(f"    - {col['name']} ({col['type']}){samples_str}")
            lines.append("")

        return "\n".join(lines)


# Global instance
crawler = SchemaCrawler()
