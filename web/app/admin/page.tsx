"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, ShieldCheck, Sparkles, ScrollText, RefreshCw } from "lucide-react";

interface AuditLogEntry {
  log_id: string;
  user_email?: string;
  role?: string;
  question: string;
  generated_sql?: string;
  execution_status: string;
  rows_returned: number;
  latency_ms: number;
  created_at?: string;
}

interface GoldenQueryEntry {
  id?: number;
  question: string;
  sql: string;
  category?: string;
}

interface RoleEntry {
  name: string;
  description: string;
  allowed_tables: string[];
  denied_columns: Record<string, string[]>;
  mask_pii: boolean;
  rls_region_scoped: boolean;
}

export default function AdminDashboardPage() {
  const [activeTab, setActiveTab] = useState<"audit" | "golden" | "roles">("audit");
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [goldenQueries, setGoldenQueries] = useState<GoldenQueryEntry[]>([]);
  const [roles, setRoles] = useState<RoleEntry[]>([]);
  const [loading, setLoading] = useState(true);

  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [logsRes, goldenRes, rolesRes] = await Promise.all([
        fetch(`${apiBase}/api/v1/admin/audit-logs?limit=50`).then((r) => r.json()).catch(() => ({ logs: [] })),
        fetch(`${apiBase}/api/v1/admin/golden-queries`).then((r) => r.json()).catch(() => ({ golden_queries: [] })),
        fetch(`${apiBase}/api/v1/admin/roles`).then((r) => r.json()).catch(() => ({ roles: [] })),
      ]);
      setLogs(logsRes.logs || []);
      setGoldenQueries(goldenRes.golden_queries || []);
      setRoles(rolesRes.roles || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 overflow-y-auto">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center space-x-4">
            <Link
              href="/"
              className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700 text-sm"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Analyst</span>
            </Link>
            <div>
              <h1 className="text-xl font-bold text-white flex items-center space-x-2">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                <span>AskLens Governance & Admin Console</span>
              </h1>
              <p className="text-xs text-slate-400">
                Audit Logs, Golden Query Few-Shot Registry, and RBAC/RLS Policies
              </p>
            </div>
          </div>
          <button
            onClick={fetchAll}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-medium text-white"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </button>
        </div>

        {/* Tabs */}
        <div className="flex space-x-2">
          <button
            onClick={() => setActiveTab("audit")}
            className={`inline-flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium ${
              activeTab === "audit"
                ? "bg-indigo-600 text-white"
                : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            <ScrollText className="w-4 h-4" />
            <span>Audit Logs ({logs.length})</span>
          </button>
          <button
            onClick={() => setActiveTab("golden")}
            className={`inline-flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium ${
              activeTab === "golden"
                ? "bg-indigo-600 text-white"
                : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            <Sparkles className="w-4 h-4" />
            <span>Golden Queries ({goldenQueries.length})</span>
          </button>
          <button
            onClick={() => setActiveTab("roles")}
            className={`inline-flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium ${
              activeTab === "roles"
                ? "bg-indigo-600 text-white"
                : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            <ShieldCheck className="w-4 h-4" />
            <span>RBAC Roles ({roles.length})</span>
          </button>
        </div>

        {/* Audit Logs View */}
        {activeTab === "audit" && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
            {logs.length === 0 ? (
              <div className="p-8 text-center text-slate-400 text-sm">
                No audit logs recorded yet. Run a query in the Analyst chat to populate logs.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950 text-slate-400 uppercase border-b border-slate-800">
                    <tr>
                      <th className="px-4 py-3">Role / User</th>
                      <th className="px-4 py-3">Question</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">Rows</th>
                      <th className="px-4 py-3">Latency</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {logs.map((log) => (
                      <tr key={log.log_id} className="hover:bg-slate-800/40">
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className="px-2 py-0.5 rounded bg-slate-800 text-indigo-300 font-mono">
                            {log.role || "analyst"}
                          </span>
                          <div className="text-[11px] text-slate-500 mt-0.5">{log.user_email}</div>
                        </td>
                        <td className="px-4 py-3 max-w-md">
                          <div className="text-slate-200 font-medium">{log.question}</div>
                          {log.generated_sql && (
                            <pre className="mt-1 text-[10px] text-slate-400 font-mono truncate max-w-md">
                              {log.generated_sql}
                            </pre>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[11px] font-medium ${
                              log.execution_status === "success"
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                                : "bg-rose-500/10 text-rose-400 border border-rose-500/30"
                            }`}
                          >
                            {log.execution_status}
                          </span>
                        </td>
                        <td className="px-4 py-3 font-mono text-slate-300">{log.rows_returned}</td>
                        <td className="px-4 py-3 font-mono text-slate-300">{log.latency_ms} ms</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Golden Queries View */}
        {activeTab === "golden" && (
          <div className="grid gap-4">
            {goldenQueries.map((gq, idx) => (
              <div key={idx} className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-white">{gq.question}</span>
                  <span className="text-[11px] px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/30">
                    {gq.category || "Verified"}
                  </span>
                </div>
                <pre className="p-3 rounded-lg bg-slate-950 text-emerald-300 text-xs font-mono overflow-x-auto">
                  {gq.sql}
                </pre>
              </div>
            ))}
          </div>
        )}

        {/* Roles View */}
        {activeTab === "roles" && (
          <div className="grid md:grid-cols-3 gap-4">
            {roles.map((r) => (
              <div key={r.name} className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-white uppercase tracking-wide">{r.name}</h3>
                  <span className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                    {r.mask_pii ? "PII Masked" : "Full PII"}
                  </span>
                </div>
                <p className="text-xs text-slate-400">{r.description}</p>
                <div>
                  <div className="text-[11px] font-semibold text-slate-500 uppercase mb-1">
                    Allowed Tables
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {r.allowed_tables.map((t) => (
                      <span key={t} className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-emerald-300 font-mono">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
                {Object.keys(r.denied_columns).length > 0 && (
                  <div>
                    <div className="text-[11px] font-semibold text-slate-500 uppercase mb-1">
                      Restricted Columns
                    </div>
                    <div className="text-xs font-mono text-rose-300">
                      {Object.entries(r.denied_columns)
                        .map(([tbl, cols]) => `${tbl}: ${cols.join(", ")}`)
                        .join(" | ")}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
