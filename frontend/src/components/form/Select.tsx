import type React from "react";
import { type SelectHTMLAttributes, forwardRef } from "react";
import { ChevronDownIcon } from "@/icons";

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, "size"> {
  options: SelectOption[];
  placeholder?: string;
  error?: boolean;
}

const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ options, placeholder = "Pilih salah satu...", error = false, disabled = false, className = "", value, ...props }, ref) => {
    return (
      <div className="relative w-full">
        <select
          ref={ref}
          value={value}
          disabled={disabled}
          className={`h-11 w-full appearance-none rounded-lg border text-sm shadow-theme-xs ps-4 pe-11 py-2.5 transition-colors focus:outline-hidden focus:ring-3 ${
            disabled
              ? "border-gray-300 bg-gray-100 text-gray-400 opacity-60 cursor-not-allowed dark:border-gray-700 dark:bg-gray-800"
              : error
              ? "border-error-500 text-gray-800 focus:border-error-300 focus:ring-error-500/20 dark:border-error-500 dark:text-white/90"
              : "border-gray-300 bg-transparent text-gray-800 focus:border-brand-300 focus:ring-brand-500/20 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90"
          } ${className}`}
          {...props}
        >
          {placeholder && (
            <option value="" disabled className="text-gray-400 dark:bg-gray-900">
              {placeholder}
            </option>
          )}
          {options.map((opt) => (
            <option key={opt.value} value={opt.value} disabled={opt.disabled} className="text-gray-800 dark:bg-gray-900 dark:text-gray-200">
              {opt.label}
            </option>
          ))}
        </select>
        <span className="pointer-events-none absolute inset-y-0 end-3.5 flex items-center text-gray-400">
          <ChevronDownIcon className="w-4 h-4" />
        </span>
      </div>
    );
  }
);

Select.displayName = "Select";
export default Select;