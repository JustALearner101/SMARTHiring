"use client";

import Checkbox from "@/components/form/input/Checkbox";
import Input from "@/components/form/input/InputField";
import Label from "@/components/form/Label";
import Button from "@/components/ui/button/Button";
import { useAuth } from "@/context/AuthContext";
import { Link, useRouter } from "@/i18n/navigation";
import { ChevronLeftIcon, EyeCloseIcon, EyeIcon } from "@/icons";
import React, { useState } from "react";

export default function SignInForm() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isChecked, setIsChecked] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { login } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setErrorMessage("Harap masukkan username dan password.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      await login({ username: username.trim(), password });
      router.push("/orchestration/scheduling");
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Gagal login. Periksa kembali kredensial Anda.";
      setErrorMessage(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex w-full flex-1 flex-col lg:w-1/2">
      <div className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center">
        <div>
          <div className="mb-6 sm:mb-8">
            <span className="inline-flex items-center rounded-md bg-brand-50 px-2.5 py-1 text-xs font-semibold text-brand-700 dark:bg-brand-500/15 dark:text-brand-300 mb-2">
              Heketon Office Ops AI
            </span>
            <h1 className="mb-2 text-title-sm font-bold text-gray-900 sm:text-title-md dark:text-white/90">
              Sign In to Your Workspace
            </h1>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Sign in as an HR Admin, Hiring Manager, or Auditor to manage interview scheduling and reviews.
            </p>
          </div>

          {/* Error Banner */}

          {errorMessage && (
            <div className="mb-5 rounded-xl border border-error-200 bg-error-50 p-3 text-xs text-error-700 dark:border-error-800 dark:bg-error-950/30 dark:text-error-400">
              {errorMessage}
            </div>
          )}

          {/* Traditional Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label>
                Username<span className="text-error-500">*</span>
              </Label>
              <Input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. hr.admin or budi.santoso"
                required
              />
            </div>

            <div>
              <Label>
                Password <span className="text-error-500">*</span>
              </Label>
              <div className="relative">
                <Input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password (default: password123)"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="inset-e-4 absolute top-1/2 z-30 -translate-y-1/2 cursor-pointer text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? (
                    <EyeIcon className="fill-gray-500 dark:fill-gray-400" />
                  ) : (
                    <EyeCloseIcon className="fill-gray-500 dark:fill-gray-400" />
                  )}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between pt-1">
              <div className="flex items-center gap-2">
                <Checkbox checked={isChecked} onChange={setIsChecked} />
                <span className="text-xs text-gray-600 dark:text-gray-400">
                  Ingat sesi saya
                </span>
              </div>
            </div>

            <Button
              type="submit"
              className="w-full mt-2"
              size="md"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Memverifikasi Kredensial..." : "Sign In to Workspace"}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
