"use client";

import React, { useState } from "react";
import { Download, Table as TableIcon, ChevronLeft, ChevronRight } from "lucide-react";
import { exportToCSV } from "@/lib/utils";

interface DataTableProps {
  columns: string[];
  rows: Record<string, any>[];
  totalRows: number;
  tableName?: string;
}

export const DataTable: React.FC<DataTableProps> = ({
  columns,
  rows,
  totalRows,
  tableName = "analysis_result",
}) => {
  const [page, setPage] = useState(0);
  const pageSize = 10;
  const pageCount = Math.ceil(rows.length / pageSize);
  const currentRows = rows.slice(page * pageSize, (page + 1) * pageSize);

  if (!columns || columns.length === 0 || !rows || rows.length === 0) {
    return null;
  }

  return (
    <div className="border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden my-3 bg-white dark:bg-slate-900 shadow-sm text-xs">
      <div className="flex items-center justify-between px-3 py-2 bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center space-x-2 text-slate-700 dark:text-slate-300 font-medium">
          <TableIcon className="w-4 h-4 text-slate-500" />
          <span>Results Preview</span>
          <span className="text-[11px] text-slate-500">
            ({rows.length} {rows.length === totalRows ? "rows" : `of ${totalRows} rows`})
          </span>
        </div>

        <button
          onClick={() => exportToCSV(tableName, rows, columns)}
          className="flex items-center space-x-1 px-2 py-1 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors text-slate-700 dark:text-slate-300 font-medium"
        >
          <Download className="w-3.5 h-3.5 text-blue-500" />
          <span>Download CSV</span>
        </button>
      </div>

      <div className="overflow-x-auto max-h-72">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-100/70 dark:bg-slate-800/80 text-slate-600 dark:text-slate-400 font-semibold border-b border-slate-200 dark:border-slate-800">
              {columns.map((col) => (
                <th key={col} className="p-2.5 whitespace-nowrap">
                  {col.replace(/_/g, " ").toUpperCase()}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {currentRows.map((row, rIdx) => (
              <tr
                key={rIdx}
                className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
              >
                {columns.map((col) => {
                  const val = row[col];
                  const formatted =
                    typeof val === "number"
                      ? Number.isInteger(val)
                        ? val.toLocaleString()
                        : val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                      : val === null || val === undefined
                      ? "-"
                      : String(val);

                  return (
                    <td key={col} className="p-2.5 whitespace-nowrap text-slate-700 dark:text-slate-300">
                      {formatted}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {pageCount > 1 && (
        <div className="flex items-center justify-between px-3 py-2 bg-slate-50 dark:bg-slate-800/50 border-t border-slate-200 dark:border-slate-800 text-[11px] text-slate-500">
          <span>
            Page {page + 1} of {pageCount}
          </span>
          <div className="flex items-center space-x-1">
            <button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
              className="p-1 rounded hover:bg-slate-200 dark:hover:bg-slate-700 disabled:opacity-30"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setPage(Math.min(pageCount - 1, page + 1))}
              disabled={page >= pageCount - 1}
              className="p-1 rounded hover:bg-slate-200 dark:hover:bg-slate-700 disabled:opacity-30"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
