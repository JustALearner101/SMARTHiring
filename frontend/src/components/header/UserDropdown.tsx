"use client";

import { useAuth } from "@/context/AuthContext";
import { Link } from "@/i18n/navigation";
import { ChevronDownIcon } from "@/icons";
import { useState } from "react";
import { Dropdown } from "../ui/dropdown/Dropdown";

export default function UserDropdown() {
  const [isOpen, setIsOpen] = useState(false);

  const { user, role, logout } = useAuth();

  const toggleDropdown = () => {
    setIsOpen(!isOpen);
  };

  const closeDropdown = () => {
    setIsOpen(false);
  };

  const getRoleBadge = (r: string | null | undefined) => {
    switch (r) {
      case "HR":
        return (
          <span className="rounded-md bg-success-50 px-2 py-0.5 text-[10px] font-bold text-success-700 dark:bg-success-500/15 dark:text-success-400">
            HR LEAD
          </span>
        );
      case "INTERVIEWER":
        return (
          <span className="rounded-md bg-blue-light-50 px-2 py-0.5 text-[10px] font-bold text-blue-light-700 dark:bg-blue-light-500/15 dark:text-blue-light-400">
            INTERVIEWER
          </span>
        );
      case "ADMIN":
        return (
          <span className="rounded-md bg-brand-50 px-2 py-0.5 text-[10px] font-bold text-brand-700 dark:bg-brand-500/15 dark:text-brand-400">
            SYSTEM ADMIN
          </span>
        );
      default:
        return (
          <span className="rounded-md bg-gray-100 px-2 py-0.5 text-[10px] font-bold text-gray-600 dark:bg-gray-800 dark:text-gray-400">
            GUEST
          </span>
        );
    }
  };

  const displayName = user?.name || "Demo User";
  const initials = displayName
    .split(" ")
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <div className="relative">
      <button
        onClick={toggleDropdown}
        className="dropdown-toggle flex items-center gap-2 text-gray-700 dark:text-gray-400"
      >
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand-500 font-bold text-xs text-white shadow-theme-xs">
          {initials}
        </span>

        <div className="hidden text-start sm:block">
          <span className="block text-theme-sm font-semibold text-gray-800 dark:text-white/90 leading-tight">
            {displayName}
          </span>
          <div className="mt-0.5">{getRoleBadge(role)}</div>
        </div>

        <ChevronDownIcon
          className={`size-4 text-gray-500 transition-transform duration-200 dark:text-gray-400 ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      <Dropdown
        isOpen={isOpen}
        onClose={closeDropdown}
        className="absolute mt-4.25 flex w-72 flex-col rounded-2xl border border-gray-200 bg-white p-3 shadow-theme-lg ltr:right-0 rtl:right-auto rtl:left-0 dark:border-gray-800 dark:bg-gray-dark"
      >
        <div className="border-b border-gray-100 pb-3 dark:border-gray-800">
          <div className="flex items-center justify-between">
            <span className="block text-theme-sm font-bold text-gray-800 dark:text-white">
              {displayName}
            </span>
            {getRoleBadge(role)}
          </div>
          <span className="mt-0.5 block text-theme-xs text-gray-500 dark:text-gray-400">
            {user?.email || "Belum login"}
          </span>
          <span className="mt-1 block text-[11px] text-gray-400 dark:text-gray-500">
            Dept: {user?.department || "General"}
          </span>
        </div>

        {/* Logout / Login Button */}
        {user ? (
          <button
            type="button"
            onClick={() => {
              logout();
              closeDropdown();
            }}
            className="group mt-3 flex w-full items-center justify-center gap-2 rounded-lg border border-error-200 bg-error-50/50 px-3 py-2 text-theme-sm font-semibold text-error-700 transition-colors hover:bg-error-100 hover:text-error-800 dark:border-error-800 dark:bg-error-950/20 dark:text-error-400 dark:hover:bg-error-950/40"
          >
            <svg
              className="size-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
              />
            </svg>
            <span>Sign Out</span>
          </button>
        ) : (
          <Link
            href="/signin"
            onClick={closeDropdown}
            className="group mt-3 flex items-center justify-center gap-2 rounded-lg bg-brand-500 px-3 py-2 text-theme-sm font-semibold text-white shadow-theme-xs hover:bg-brand-600"
          >
            <span>Sign In to Workspace</span>
          </Link>
        )}
      </Dropdown>
    </div>
  );
}
