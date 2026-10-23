import type React from "react";
import { type TextareaHTMLAttributes, forwardRef } from "react";

export interface TextAreaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean;
  hint?: string;
}

const TextArea = forwardRef<HTMLTextAreaElement, TextAreaProps>(
  ({ className = "", disabled = false, error = false, hint, rows = 3, ...props }, ref) => {
    let stateClasses = "border-gray-300 bg-transparent text-gray-800 focus:border-brand-300 focus:ring-brand-500/20 dark:border-gray-700 dark:text-white/90 dark:focus:border-brand-800";

    if (disabled) {
      stateClasses = "border-gray-300 bg-gray-100 text-gray-400 opacity-60 cursor-not-allowed dark:border-gray-700 dark:bg-gray-800 dark:text-gray-500";
    } else if (error) {
      stateClasses = "border-error-500 text-gray-800 focus:border-error-300 focus:ring-error-500/20 dark:border-error-500 dark:text-white/90";
    }

    return (
      <div className="relative w-full">
        <textarea
          ref={ref}
          rows={rows}
          disabled={disabled}
          className={`w-full rounded-lg border text-sm shadow-theme-xs appearance-none transition-colors px-4 py-2.5 placeholder:text-gray-400 focus:outline-hidden focus:ring-3 dark:bg-gray-900 dark:placeholder:text-white/30 ${stateClasses} ${className}`}
          {...props}
        />
        {hint && (
          <p
            className={`mt-1.5 text-xs ${
              error ? "text-error-500" : "text-gray-500 dark:text-gray-400"
            }`}
          >
            {hint}
          </p>
        )}
      </div>
    );
  }
);

TextArea.displayName = "TextArea";
export default TextArea;