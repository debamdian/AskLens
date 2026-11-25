"use client";

import React from "react";
import { CheckCircle2, Loader2, Sparkles, Database, FileCode, BarChart3 } from "lucide-react";

interface StepProgressProps {
  status: string;
  message?: string;
  plan?: { steps: string[] };
}

export const StepProgress: React.FC<StepProgressProps> = ({ status, message, plan }) => {
  const isFinished = status === "completed";

  const getStepIcon = (stepStatus: string) => {
    switch (stepStatus) {
      case "planning":
        return <Sparkles className="w-4 h-4 text-amber-500 animate-pulse" />;
      case "generating_sql":
        return <FileCode className="w-4 h-4 text-blue-500 animate-pulse" />;
      case "executing":
        return <Database className="w-4 h-4 text-purple-500 animate-pulse" />;
      case "synthesizing":
        return <BarChart3 className="w-4 h-4 text-emerald-500 animate-pulse" />;
      default:
        return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
    }
  };

  return (
    <div className="bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 rounded-lg p-3 my-2 text-xs space-y-2">
      <div className="flex items-center space-x-2 font-medium text-slate-700 dark:text-slate-300">
        {isFinished ? (
          <CheckCircle2 className="w-4 h-4 text-emerald-500" />
        ) : (
          getStepIcon(status)
        )}
        <span>{message || "Processing analysis..."}</span>
      </div>

      {plan?.steps && plan.steps.length > 0 && (
        <details className="mt-2 text-slate-600 dark:text-slate-400">
          <summary className="cursor-pointer hover:text-blue-500 text-[11px] font-semibold">
            View Analysis Plan ({plan.steps.length} steps)
          </summary>
          <ul className="mt-1 ml-4 list-disc space-y-1 text-[11px]">
            {plan.steps.map((s, idx) => (
              <li key={idx}>{s}</li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
};
