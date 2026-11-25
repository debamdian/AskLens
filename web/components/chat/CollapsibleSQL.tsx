"use client";

import React, { useState } from "react";
import { ChevronDown, ChevronRight, Copy, Check, Terminal, ShieldCheck } from "lucide-react";

interface CollapsibleSQLProps {
  sql: string;
  executionTimeMs?: number;
  costEstimate?: number | null;
}

export const CollapsibleSQL: React.FC<CollapsibleSQLProps> = ({
  sql,
  executionTimeMs,
  costEstimate,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden my-3 bg-slate-900 text-slate-100 shadow-sm">
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between px-3 py-2 bg-slate-800/80 cursor-pointer hover:bg-slate-800 transition-colors text-xs font-mono select-none"
      >
        <div className="flex items-center space-x-2">
          {isOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
          <Terminal className="w-3.5 h-3.5 text-blue-400" />
          <span className="font-semibold text-slate-200">Executed SQL</span>
          <span className="flex items-center text-[10px] text-emerald-400 bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-800/50">
            <ShieldCheck className="w-3 h-3 mr-1 inline" /> AST Verified
          </span>
        </div>

        <div className="flex items-center space-x-3 text-[11px] text-slate-400">
          {executionTimeMs !== undefined && (
            <span>Latency: {executionTimeMs.toFixed(1)}ms</span>
          )}
          {costEstimate !== undefined && costEstimate !== null && (
            <span>Cost: {costEstimate.toFixed(0)}</span>
          )}
          <button
            onClick={handleCopy}
            className="flex items-center space-x-1 hover:text-slate-200 p-1 rounded"
            title="Copy SQL"
          >
            {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            <span>{copied ? "Copied" : "Copy"}</span>
          </button>
        </div>
      </div>

      {isOpen && (
        <div className="p-3 bg-slate-950 font-mono text-xs overflow-x-auto text-emerald-400 leading-relaxed border-t border-slate-800">
          <pre>{sql}</pre>
        </div>
      )}
    </div>
  );
};
