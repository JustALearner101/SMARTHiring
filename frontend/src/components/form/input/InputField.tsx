import type React from "react";
import { type InputHTMLAttributes, type ReactNode, forwardRef } from "react";

export interface InputFieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "size"> {
  error?: boolean;
  success?: boolean;
  startIcon?: ReactNode;
  endIcon?: ReactNode;
  hint?: string;
}

const InputField = forwardRef<HTMLInputElement, InputFieldProps>(
  (
    {
      className = "",
      disabled = false,
      error = false,
      success = false,
      startIcon,
      endIcon,
      hint,
      ...props
    },
    ref
  ) => {
    let stateClasses = "border-gray-300 bg-transparent text-gray-800 focus:border-brand-300 focus:ring-brand-500/20 dark:border-gray-700 dark:text-white/90 dark:focus:border-brand-800";

    if (disabled) {
      stateClasses = "border-gray-300 bg-gray-100 text-gray-400 opacity-60 cursor-not-allowed dark:border-gray-700 dark:bg-gray-800 dark:text-gray-500";
    } else if (error) {
      stateClasses = "border-error-500 text-gray-800 focus:border-error-300 focus:ring-error-500/20 dark:border-error-500 dark:text-white/90";
    } else if (success) {
      stateClasses = "border-success-500 text-gray-800 focus:border-success-300 focus:ring-success-500/20 dark:border-success-500 dark:text-white/90";
    }

    return (
      <div className="relative w-full">
        {startIcon && (
          <span className="pointer-events-none absolute inset-y-0 start-0 flex items-center ps-3.5 text-gray-400">
            {startIcon}
          </span>
        )}

        <input
          ref={ref}
          disabled={disabled}
          className={`h-11 w-full rounded-lg border text-sm shadow-theme-xs appearance-none transition-colors placeholder:text-gray-400 focus:outline-hidden focus:ring-3 dark:bg-gray-900 dark:placeholder:text-white/30 ${
            startIcon ? "ps-10" : "ps-4"
          } ${endIcon ? "pe-10" : "pe-4"} py-2.5 ${stateClasses} ${className}`}
          {...props}
        />

        {endIcon && (
          <span className="pointer-events-none absolute inset-y-0 end-0 flex items-center pe-3.5 text-gray-400">
            {endIcon}
          </span>
        )}

        {hint && (
          <p
            className={`mt-1.5 text-xs ${
              error
                ? "text-error-500"
                : success
                ? "text-success-500"
                : "text-gray-500 dark:text-gray-400"
            }`}
          >
            {hint}
          </p>
        )}
      </div>
    );
  }
);

InputField.displayName = "InputField";
export default InputField;