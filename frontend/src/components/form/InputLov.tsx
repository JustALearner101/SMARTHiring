"use client";

import type React from "react";
import { useState, useRef, useMemo, useEffect } from "react";
import { ChevronDownIcon, CloseIcon } from "@/icons";

export interface LovOption {
  value: string;
  label: string;
  description?: string;
  badge?: string;
}

export interface InputLovProps {
  id?: string;
  options: LovOption[];
  value?: string;
  placeholder?: string;
  searchPlaceholder?: string;
  disabled?: boolean;
  error?: boolean;
  onChange: (value: string, selectedOption?: LovOption) => void;
  className?: string;
}

const InputLov: React.FC<InputLovProps> = ({
  id,
  options,
  value,
  placeholder = "Pilih salah satu...",
  searchPlaceholder = "Cari data...",
  disabled = false,
  error = false,
  onChange,
  className = "",
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const selectedOption = useMemo(
    () => options.find((opt) => opt.value === value),
    [options, value]
  );

  const filteredOptions = useMemo(() => {
    if (!searchQuery.trim()) return options;
    const q = searchQuery.toLowerCase();
    return options.filter(
      (opt) =>
        opt.label.toLowerCase().includes(q) ||
        (opt.description && opt.description.toLowerCase().includes(q))
    );
  }, [options, searchQuery]);

  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener("mousedown", handleOutsideClick);
      setTimeout(() => searchInputRef.current?.focus(), 50);
    }
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, [isOpen]);

  const handleSelect = (option: LovOption) => {
    onChange(option.value, option);
    setIsOpen(false);
    setSearchQuery("");
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChange("");
  };

  return (
    <div ref={containerRef} className={`relative w-full ${className}`}>
      <button
        type="button"
        id={id}
        disabled={disabled}
        onClick={() => !disabled && setIsOpen((prev) => !prev)}
        className={`h-11 w-full flex items-center justify-between rounded-lg border appearance-none ps-4 pe-3 py-2.5 text-sm shadow-theme-xs transition-colors text-start focus:outline-hidden focus:ring-3 ${
          disabled
            ? "bg-gray-100 text-gray-400 border-gray-300 cursor-not-allowed dark:bg-gray-800 dark:border-gray-700"
            : error
            ? "border-error-500 focus:border-error-300 focus:ring-error-500/20 dark:border-error-500"
            : "bg-transparent border-gray-300 focus:border-brand-300 focus:ring-brand-500/20 dark:border-gray-700 dark:bg-gray-900"
        }`}
      >
        <span className={selectedOption ? "text-gray-800 dark:text-white/90" : "text-gray-400 dark:text-white/30"}>
          {selectedOption ? selectedOption.label : placeholder}
        </span>

        <div className="flex items-center gap-1.5 ms-2 text-gray-400">
          {selectedOption && !disabled && (
            <span
              onClick={handleClear}
              className="p-1 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
            >
              <CloseIcon className="w-3.5 h-3.5" />
            </span>
          )}
          <ChevronDownIcon className={`w-4 h-4 transition-transform ${isOpen ? "rotate-180" : ""}`} />
        </div>
      </button>

      {isOpen && (
        <div className="absolute z-99 mt-1.5 w-full rounded-xl border border-gray-200 bg-white shadow-theme-lg dark:border-gray-700 dark:bg-gray-900 overflow-hidden animate-in fade-in zoom-in-95 duration-100">
          <div className="p-2 border-b border-gray-100 dark:border-gray-800">
            <input
              ref={searchInputRef}
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={searchPlaceholder}
              className="w-full rounded-lg bg-gray-50 px-3 py-2 text-xs text-gray-800 outline-hidden dark:bg-gray-800 dark:text-gray-200 placeholder:text-gray-400 focus:ring-2 focus:ring-brand-500/20"
            />
          </div>

          <div className="max-h-60 overflow-y-auto p-1.5 custom-scrollbar">
            {filteredOptions.length === 0 ? (
              <div className="py-4 text-center text-xs text-gray-400">
                Tidak ada data yang cocok
              </div>
            ) : (
              filteredOptions.map((opt) => {
                const isSelected = opt.value === value;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => handleSelect(opt)}
                    className={`w-full flex items-center justify-between rounded-lg px-3 py-2 text-start text-xs transition-colors ${
                      isSelected
                        ? "bg-brand-50 text-brand-600 font-medium dark:bg-brand-500/15 dark:text-brand-400"
                        : "text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
                    }`}
                  >
                    <div>
                      <div className="font-medium">{opt.label}</div>
                      {opt.description && (
                        <div className="text-[11px] text-gray-400 dark:text-gray-500">{opt.description}</div>
                      )}
                    </div>
                    {opt.badge && (
                      <span className="ms-2 rounded bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-600 dark:bg-gray-800 dark:text-gray-400">
                        {opt.badge}
                      </span>
                    )}
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default InputLov;