import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function exportToCSV(filename: string, rows: Record<string, any>[], columns: string[]) {
  if (!rows || rows.length === 0) return;

  const header = columns.join(",");
  const csvContent = rows
    .map((row) =>
      columns
        .map((col) => {
          const val = row[col] === null || row[col] === undefined ? "" : String(row[col]);
          return `"${val.replace(/"/g, '""')}"`;
        })
        .join(",")
    )
    .join("\n");

  const blob = new Blob([`${header}\n${csvContent}`], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", `${filename}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
