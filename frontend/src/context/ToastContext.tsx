"use client";

import React, { createContext, useCallback, useContext, useState } from "react";

export type ToastType = "success" | "error" | "warning" | "info";

export interface ToastItem {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
}

interface ToastContextType {
  toasts: ToastItem[];
  showToast: (type: ToastType, title: string, message?: string) => void;
  showSuccess: (title: string, message?: string) => void;
  showError: (title: string, message?: string) => void;
  showWarning: (title: string, message?: string) => void;
  showInfo: (title: string, message?: string) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback(
    (type: ToastType, title: string, message?: string) => {
      const id = `toast-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;
      const newToast: ToastItem = { id, type, title, message };
      setToasts((prev) => [...prev, newToast]);

      setTimeout(() => {
        removeToast(id);
      }, 4500);
    },
    [removeToast]
  );

  const showSuccess = useCallback(
    (title: string, message?: string) => showToast("success", title, message),
    [showToast]
  );

  const showError = useCallback(
    (title: string, message?: string) => showToast("error", title, message),
    [showToast]
  );

  const showWarning = useCallback(
    (title: string, message?: string) => showToast("warning", title, message),
    [showToast]
  );

  const showInfo = useCallback(
    (title: string, message?: string) => showToast("info", title, message),
    [showToast]
  );

  return (
    <ToastContext.Provider
      value={{
        toasts,
        showToast,
        showSuccess,
        showError,
        showWarning,
        showInfo,
        removeToast,
      }}
    >
      {children}
      {/* Toast Floating Viewport */}
      <div className="fixed top-5 end-5 z-99999 flex flex-col gap-2.5 max-w-sm w-full pointer-events-none p-4 sm:p-0">
        {toasts.map((toast) => {
          const typeStyles = {
            success: {
              border: "border-success-500",
              bg: "bg-white dark:bg-gray-900",
              text: "text-success-700 dark:text-success-400",
              iconBg: "bg-success-100 text-success-600 dark:bg-success-500/20 dark:text-success-300",
              icon: (
                <svg className="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7" />
                </svg>
              ),
            },
            error: {
              border: "border-error-500",
              bg: "bg-white dark:bg-gray-900",
              text: "text-error-700 dark:text-error-400",
              iconBg: "bg-error-100 text-error-600 dark:bg-error-500/20 dark:text-error-300",
              icon: (
                <svg className="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M6 18L18 6M6 6l12 12" />
                </svg>
              ),
            },
            warning: {
              border: "border-warning-500",
              bg: "bg-white dark:bg-gray-900",
              text: "text-warning-800 dark:text-warning-300",
              iconBg: "bg-warning-100 text-warning-700 dark:bg-warning-500/20 dark:text-warning-300",
              icon: (
                <svg className="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              ),
            },
            info: {
              border: "border-brand-500",
              bg: "bg-white dark:bg-gray-900",
              text: "text-brand-700 dark:text-brand-300",
              iconBg: "bg-brand-100 text-brand-600 dark:bg-brand-500/20 dark:text-brand-300",
              icon: (
                <svg className="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              ),
            },
          }[toast.type];

          return (
            <div
              key={toast.id}
              className={`pointer-events-auto flex items-start gap-3 rounded-2xl border-2 ${typeStyles.border} ${typeStyles.bg} p-4 shadow-theme-xl transition-all animate-in slide-in-from-top-3 fade-in duration-200`}
            >
              <div className={`flex size-8 shrink-0 items-center justify-center rounded-xl ${typeStyles.iconBg}`}>
                {typeStyles.icon}
              </div>
              <div className="flex-1 pt-0.5">
                <h5 className="text-xs font-bold text-gray-900 dark:text-white leading-tight">
                  {toast.title}
                </h5>
                {toast.message && (
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400 leading-normal">
                    {toast.message}
                  </p>
                )}
              </div>
              <button
                type="button"
                onClick={() => removeToast(toast.id)}
                className="size-6 inline-flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
              >
                <span className="sr-only">Close</span>
                <svg className="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}
