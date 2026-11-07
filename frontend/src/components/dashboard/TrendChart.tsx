"use client";

import React from "react";
import dynamic from "next/dynamic";
import type { ApexOptions } from "apexcharts";
import type { TrendPoint } from "@/services/dashboardService";

const ReactApexChart = dynamic(() => import("react-apexcharts"), {
  ssr: false,
});

interface TrendChartProps {
  data: TrendPoint[];
}

export function TrendChart({ data }: TrendChartProps) {
  const categories = data.map((d) => d.week_label);
  const seriesData = data.map((d) => d.count);

  const options: ApexOptions = {
    chart: {
      fontFamily: "Outfit, sans-serif",
      type: "area",
      height: 240,
      width: "100%",
      toolbar: { show: false },
    },
    colors: ["#465fff"],
    stroke: {
      curve: "smooth",
      width: 2.5,
    },
    fill: {
      type: "gradient",
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.45,
        opacityTo: 0.05,
        stops: [0, 95, 100],
      },
    },
    dataLabels: { enabled: false },
    grid: {
      borderColor: "#e5e7eb",
      strokeDashArray: 4,
      xaxis: { lines: { show: false } },
      yaxis: { lines: { show: true } },
    },
    xaxis: {
      categories: categories.length > 0 ? categories : ["W1", "W2", "W3", "W4"],
      axisBorder: { show: false },
      axisTicks: { show: false },
      labels: {
        style: {
          colors: "#9ca3af",
          fontSize: "12px",
        },
      },
    },
    yaxis: {
      labels: {
        style: {
          colors: "#9ca3af",
          fontSize: "12px",
        },
      },
    },
    tooltip: {
      theme: "light",
      y: {
        formatter: (val: number) => `${val} Kandidat`,
      },
    },
  };

  const series = [
    {
      name: "Aplikasi Baru",
      data: seriesData.length > 0 ? seriesData : [0, 0, 0, 0],
    },
  ];

  return (
    <div className="h-full rounded-2xl border border-gray-200 bg-white p-5 md:p-6 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900 overflow-hidden">
      <div className="flex items-center justify-between pb-2">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Trends in Candidate Applications
          </h3>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            Number of new applicants per week (last 8 weeks)
          </p>
        </div>
      </div>

      <div className="mt-2 -ms-4 max-w-full overflow-hidden">
        <ReactApexChart
          options={options}
          series={series}
          type="area"
          height={240}
          width="100%"
        />
      </div>
    </div>
  );
}

