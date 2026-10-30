"use client";

import React from "react";
import { ChevronLeftIcon } from "@/icons";

export interface TablePaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  pageSizeOptions?: number[];
  isLoading?: boolean;
  className?: string;
}

export default function TablePagination({
  currentPage,
  totalPages,
  totalItems,
  pageSize,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions = [10, 20, 50],
  isLoading = false,
  className = "",
}: TablePaginationProps) {
  if (totalItems <= 0) return null;

  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalItems);

  // Generate page numbers with ellipsis
  const getPageNumbers = () => {
    const pages: (number | string)[] = [];
    if (totalPages <= 5) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      pages.push(1);
      if (currentPage > 3) pages.push("...");
      const start = Math.max(2, currentPage - 1);
      const end = Math.min(totalPages - 1, currentPage + 1);
      for (let i = start; i <= end; i++) pages.push(i);
      if (currentPage < totalPages - 2) pages.push("...");
      pages.push(totalPages);
    }
    return pages;
  };

  return (
    <div
      className={`flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between px-5 sm:px-6 py-4 border-t border-gray-100 dark:border-gray-800 text-xs text-gray-500 dark:text-gray-400 bg-white dark:bg-gray-900 ${className}`}
    >
      {/* Left side: Results counter & page size selector */}
      <div className="flex flex-wrap items-center gap-3">
        <span>
          Showing <strong className="text-gray-900 dark:text-white">{startItem}</strong> to{" "}
          <strong className="text-gray-900 dark:text-white">{endItem}</strong> of{" "}
          <strong className="text-gray-900 dark:text-white">{totalItems}</strong> records
        </span>

        {onPageSizeChange && (
          <div className="flex items-center gap-1.5 ms-2">
            <span>Rows:</span>
            <select
              value={pageSize}
              onChange={(e) => onPageSizeChange(Number(e.target.value))}
              disabled={isLoading}
              className="rounded-lg border border-gray-200 bg-white px-2 py-1 text-xs font-semibold text-gray-700 shadow-theme-xs focus:border-brand-500 focus:outline-hidden dark:border-gray-800 dark:bg-gray-800 dark:text-gray-200"
            >
              {pageSizeOptions.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Right side: Page navigation buttons */}
      <div className="flex items-center gap-1.5">
        <button
          type="button"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage <= 1 || isLoading}
          title="Previous Page"
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-600 shadow-theme-xs transition-colors hover:bg-gray-50 disabled:opacity-40 dark:border-gray-800 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
        >
          <ChevronLeftIcon className="h-4 w-4" />
        </button>

        {getPageNumbers().map((p, idx) =>
          typeof p === "number" ? (
            <button
              key={idx}
              type="button"
              onClick={() => onPageChange(p)}
              disabled={isLoading}
              className={`flex h-8 min-w-[32px] px-2 items-center justify-center rounded-lg font-semibold shadow-theme-xs transition-colors ${
                currentPage === p
                  ? "bg-brand-500 text-white"
                  : "border border-gray-200 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-800 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
              }`}
            >
              {p}
            </button>
          ) : (
            <span key={idx} className="px-1 text-gray-400">
              ...
            </span>
          )
        )}

        <button
          type="button"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages || isLoading}
          title="Next Page"
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-600 shadow-theme-xs transition-colors hover:bg-gray-50 disabled:opacity-40 dark:border-gray-800 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
        >
          <ChevronLeftIcon className="h-4 w-4 rotate-180" />
        </button>
      </div>
    </div>
  );
}
