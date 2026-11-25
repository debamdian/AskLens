"use client";

import React from "react";
import { User, Bot, ThumbsUp, ThumbsDown, MessageSquareShare } from "lucide-react";
import { StepProgress } from "./StepProgress";
import { CollapsibleSQL } from "./CollapsibleSQL";
import { DataTable } from "./DataTable";
import { ChartRenderer } from "./ChartRenderer";

export interface MessageData {
  id: string;
  sender: "user" | "assistant";
  content?: string;
  status?: string;
  statusMessage?: string;
  plan?: { steps: string[] };
  sql?: string;
  rowsData?: {
    columns: string[];
    rows: Record<string, any>[];
    total_rows: number;
    execution_time_ms: number;
    cost_estimate?: number | null;
  };
  chartSpec?: any;
  insight?: string;
  followUps?: string[];
}

interface MessageItemProps {
  message: MessageData;
  onFollowUpClick?: (question: string) => void;
}

export const MessageItem: React.FC<MessageItemProps> = ({ message, onFollowUpClick }) => {
  const isUser = message.sender === "user";

  if (isUser) {
    return (
      <div className="flex justify-end my-4">
        <div className="flex items-start max-w-2xl space-x-2 flex-row-reverse space-x-reverse">
          <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white shrink-0 shadow-sm">
            <User className="w-4 h-4" />
          </div>
          <div className="bg-blue-600 text-white rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm shadow-sm leading-relaxed">
            {message.content}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start my-4">
      <div className="flex items-start max-w-3xl space-x-3 w-full">
        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-600 to-blue-500 flex items-center justify-center text-white shrink-0 shadow-sm">
          <Bot className="w-4 h-4" />
        </div>

        <div className="flex-1 overflow-hidden bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl rounded-tl-sm p-4 shadow-sm text-sm text-slate-800 dark:text-slate-100 space-y-3">
          {/* Progress / Status banner */}
          {message.status && message.status !== "completed" && (
            <StepProgress
              status={message.status}
              message={message.statusMessage}
              plan={message.plan}
            />
          )}

          {/* Senior Analyst Insight */}
          {message.insight && (
            <div className="prose dark:prose-invert text-sm leading-relaxed whitespace-pre-wrap">
              {message.insight}
            </div>
          )}

          {/* Chart Spec View */}
          {message.chartSpec && <ChartRenderer spec={message.chartSpec} />}

          {/* Data Table */}
          {message.rowsData && (
            <DataTable
              columns={message.rowsData.columns}
              rows={message.rowsData.rows}
              totalRows={message.rowsData.total_rows}
            />
          )}

          {/* Collapsible Verified SQL */}
          {message.sql && (
            <CollapsibleSQL
              sql={message.sql}
              executionTimeMs={message.rowsData?.execution_time_ms}
              costEstimate={message.rowsData?.cost_estimate}
            />
          )}

          {/* Follow-up Question Chips */}
          {message.followUps && message.followUps.length > 0 && (
            <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
              <div className="flex items-center space-x-1 text-xs text-slate-500 mb-2">
                <MessageSquareShare className="w-3.5 h-3.5" />
                <span>Suggested Follow-ups</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {message.followUps.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => onFollowUpClick && onFollowUpClick(q)}
                    className="text-xs bg-slate-100 dark:bg-slate-800 hover:bg-blue-50 dark:hover:bg-blue-950/40 hover:text-blue-600 dark:hover:text-blue-400 border border-slate-200 dark:border-slate-700 px-3 py-1.5 rounded-full transition-all text-slate-700 dark:text-slate-300"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Feedback buttons */}
          {message.status === "completed" && (
            <div className="flex items-center justify-end space-x-2 text-xs text-slate-400 pt-2 border-t border-slate-50 dark:border-slate-800/50">
              <button className="p-1 hover:text-emerald-500 rounded flex items-center space-x-1">
                <ThumbsUp className="w-3.5 h-3.5" />
                <span>Good analysis</span>
              </button>
              <button className="p-1 hover:text-rose-500 rounded flex items-center space-x-1">
                <ThumbsDown className="w-3.5 h-3.5" />
                <span>Correct SQL</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
