"use client";

import React from "react";
import dynamic from "next/dynamic";
import { BarChart2 } from "lucide-react";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

interface ChartRendererProps {
  spec: {
    chart_type?: string;
    title?: string;
    xAxis?: any;
    yAxis?: any;
    series?: any[];
    tooltip?: any;
  } | null;
}

export const ChartRenderer: React.FC<ChartRendererProps> = ({ spec }) => {
  if (!spec || !spec.series || spec.series.length === 0) {
    return null;
  }

  const option = {
    title: {
      text: spec.title || "Data Visualization",
      textStyle: { fontSize: 13, fontWeight: "600", color: "#334155" },
      left: "center",
      top: 10,
    },
    tooltip: spec.tooltip || {
      trigger: spec.chart_type === "pie" ? "item" : "axis",
      backgroundColor: "rgba(15, 23, 42, 0.9)",
      textStyle: { color: "#ffffff", fontSize: 12 },
    },
    grid: {
      top: 50,
      left: "5%",
      right: "5%",
      bottom: "10%",
      containLabel: true,
    },
    xAxis: spec.xAxis || { type: "category" },
    yAxis: spec.yAxis || { type: "value" },
    series: spec.series.map((s) => ({
      ...s,
      animationDuration: 800,
      itemStyle: s.itemStyle || {
        borderRadius: [4, 4, 0, 0],
        color: "#3b82f6",
      },
    })),
  };

  return (
    <div className="border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden my-3 bg-white dark:bg-slate-900 shadow-sm p-3">
      <div className="flex items-center space-x-2 text-xs font-medium text-slate-700 dark:text-slate-300 mb-1 border-b border-slate-100 dark:border-slate-800 pb-2">
        <BarChart2 className="w-4 h-4 text-blue-500" />
        <span>Chart View</span>
      </div>
      <div className="w-full h-72">
        <ReactECharts option={option} style={{ height: "100%", width: "100%" }} />
      </div>
    </div>
  );
};
