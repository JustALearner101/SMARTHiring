import type React from "react";
import { type ReactNode } from "react";
import Label from "./Label";

export interface FormFieldProps {
  id?: string;
  label?: string;
  required?: boolean;
  error?: string;
  hint?: string;
  children: ReactNode;
  className?: string;
}

const FormField: React.FC<FormFieldProps> = ({
  id,
  label,
  required,
  error,
  hint,
  children,
  className = "",
}) => {
  return (
    <div className={`w-full ${className}`}>
      {label && (
        <div className="flex items-center justify-between mb-1.5">
          <Label htmlFor={id} className="mb-0 text-sm font-medium text-gray-700 dark:text-gray-300">
            {label}
            {required && <span className="ms-1 text-error-500">*</span>}
          </Label>
        </div>
      )}

      {children}

      {error ? (
        <p className="mt-1.5 text-xs text-error-500">{error}</p>
      ) : hint ? (
        <p className="mt-1.5 text-xs text-gray-500 dark:text-gray-400">{hint}</p>
      ) : null}
    </div>
  );
};

export default FormField;