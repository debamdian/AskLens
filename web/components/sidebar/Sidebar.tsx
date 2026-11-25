"use client";

import React, { useState, useEffect } from "react";
import {
  Database,
  BookOpen,
  History,
  Plus,
  Sparkles,
  ChevronDown,
  ChevronRight,
  Sun,
  Moon,
} from "lucide-react";

interface SidebarProps {
  onNewChat: () => void;
  onSelectSampleQuery?: (q: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ onNewChat, onSelectSampleQuery }) => {
  const [activeTab, setActiveTab] = useState<"history" | "schema" | "glossary">("history");
  const [schemaData, setSchemaData] = useState<any>(null);
  const [expandedTable, setExpandedTable] = useState<string | null>(null);
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    // Fetch schema info from backend
    fetch("http://localhost:8000/api/v1/schema/warehouse")
      .then((res) => res.json())
      .then((data) => setSchemaData(data))
      .catch(() => {});
  }, []);

  const sampleQueries = [
    "Why did sales drop in Gujarat last quarter?",
    "What are the top 5 revenue-generating product categories?",
    "Compare return rates between Gujarat and Maharashtra",
    "Show monthly marketing spend vs total order revenue",
  ];

  const glossaryItems = [
    { term: "Revenue", definition: "SUM(o.total_amount) WHERE o.status = 'completed'" },
    { term: "Return Rate", definition: "COUNT(returns) / COUNT(orders) * 100%" },
    { term: "Gross Profit", definition: "SUM(total_price - cost_amount)" },
    { term: "Active Customer", definition: "Customer with at least 1 order in the last 90 days" },
  ];

  const toggleTheme = () => {
    setIsDark(!isDark);
    if (!isDark) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  };

  return (
    <aside className="w-72 bg-slate-900 border-r border-slate-800 text-slate-200 flex flex-col h-screen select-none">
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold shadow-md shadow-blue-500/20">
            A
          </div>
          <div>
            <h1 className="font-semibold text-sm tracking-tight text-white flex items-center space-x-1">
              <span>AskLens</span>
              <span className="text-[10px] text-blue-400 font-mono bg-blue-950 px-1 rounded border border-blue-800">
                AI
              </span>
            </h1>
            <p className="text-[11px] text-slate-400">Autonomous Data Analyst</p>
          </div>
        </div>

        <button
          onClick={toggleTheme}
          className="p-1.5 rounded-md hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
          title="Toggle Theme"
        >
          {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>
      </div>

      {/* New Analysis Button */}
      <div className="p-3">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center space-x-2 bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs py-2 px-3 rounded-lg shadow-sm transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>New Analysis</span>
        </button>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-800 px-3 text-xs font-medium text-slate-400">
        <button
          onClick={() => setActiveTab("history")}
          className={`flex items-center space-x-1.5 pb-2.5 px-2 border-b-2 transition-colors ${
            activeTab === "history"
              ? "border-blue-500 text-blue-400"
              : "border-transparent hover:text-slate-300"
          }`}
        >
          <History className="w-3.5 h-3.5" />
          <span>Queries</span>
        </button>
        <button
          onClick={() => setActiveTab("schema")}
          className={`flex items-center space-x-1.5 pb-2.5 px-2 border-b-2 transition-colors ${
            activeTab === "schema"
              ? "border-blue-500 text-blue-400"
              : "border-transparent hover:text-slate-300"
          }`}
        >
          <Database className="w-3.5 h-3.5" />
          <span>Schema</span>
        </button>
        <button
          onClick={() => setActiveTab("glossary")}
          className={`flex items-center space-x-1.5 pb-2.5 px-2 border-b-2 transition-colors ${
            activeTab === "glossary"
              ? "border-blue-500 text-blue-400"
              : "border-transparent hover:text-slate-300"
          }`}
        >
          <BookOpen className="w-3.5 h-3.5" />
          <span>Glossary</span>
        </button>
      </div>

      {/* Tab Contents */}
      <div className="flex-1 overflow-y-auto p-3 text-xs space-y-4">
        {activeTab === "history" && (
          <div>
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2">
              Featured Questions
            </div>
            <div className="space-y-1.5">
              {sampleQueries.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => onSelectSampleQuery && onSelectSampleQuery(q)}
                  className="w-full text-left p-2 rounded-lg bg-slate-800/40 hover:bg-slate-800 hover:text-blue-300 transition-colors text-slate-300 leading-snug flex items-start space-x-2"
                >
                  <Sparkles className="w-3.5 h-3.5 text-blue-400 shrink-0 mt-0.5" />
                  <span>{q}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {activeTab === "schema" && (
          <div className="space-y-2">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
              Warehouse Tables
            </div>
            {schemaData?.tables ? (
              Object.entries(schemaData.tables).map(([tblName, details]: [string, any]) => {
                const isOpen = expandedTable === tblName;
                return (
                  <div
                    key={tblName}
                    className="border border-slate-800 rounded-lg overflow-hidden bg-slate-950/40"
                  >
                    <div
                      onClick={() => setExpandedTable(isOpen ? null : tblName)}
                      className="p-2 flex items-center justify-between hover:bg-slate-800/60 cursor-pointer font-mono text-[11px]"
                    >
                      <span className="text-blue-300 font-semibold">{tblName}</span>
                      {isOpen ? (
                        <ChevronDown className="w-3 h-3 text-slate-500" />
                      ) : (
                        <ChevronRight className="w-3 h-3 text-slate-500" />
                      )}
                    </div>
                    {isOpen && details.columns && (
                      <div className="p-2 bg-slate-900 border-t border-slate-800 space-y-1 text-[10px] text-slate-400 font-mono">
                        {details.columns.map((c: any) => (
                          <div key={c.name} className="flex justify-between">
                            <span className="text-slate-300">{c.name}</span>
                            <span className="text-slate-500">{c.type}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })
            ) : (
              <p className="text-slate-500 text-xs">Loading warehouse schema...</p>
            )}
          </div>
        )}

        {activeTab === "glossary" && (
          <div className="space-y-2.5">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
              Semantic Glossary
            </div>
            {glossaryItems.map((item, idx) => (
              <div key={idx} className="p-2.5 rounded-lg bg-slate-800/40 border border-slate-800">
                <div className="font-semibold text-slate-200 text-xs">{item.term}</div>
                <div className="text-[11px] text-slate-400 font-mono mt-1 leading-snug">
                  {item.definition}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Role / User indicator */}
      <div className="p-3 border-t border-slate-800 bg-slate-950/50 flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
          <span>Role: Senior Analyst</span>
        </div>
        <span className="font-mono text-[10px] text-slate-500">PostgreSQL</span>
      </div>
    </aside>
  );
};
