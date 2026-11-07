"use client";

import { useAuth } from "@/context/AuthContext";
import { useSidebar } from "@/context/SidebarContext";
import { SimulatorProvider } from "@/context/SimulatorContext";
import { usePathname, useRouter } from "@/i18n/navigation";
import AppHeader from "@/layout/AppHeader";
import AppSidebar from "@/layout/AppSidebar";
import Backdrop from "@/layout/Backdrop";
import { isRouteAllowedForRole } from "@/utils/rbac";
import React, { useEffect } from "react";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isExpanded, isHovered, isMobileOpen } = useSidebar();
  const { token, role, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  const isRouteAllowed = token && role ? isRouteAllowedForRole(pathname, role) : false;

  useEffect(() => {
    if (!isLoading && !token) {
      router.replace("/signin");
      return;
    }
    if (!isLoading && token && role && !isRouteAllowedForRole(pathname, role)) {
      router.replace("/");
    }
  }, [isLoading, token, role, pathname, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="flex flex-col items-center gap-3">
          <div className="size-8 animate-spin rounded-full border-4 border-brand-500 border-t-transparent" />
          <p className="text-xs font-semibold text-gray-500 dark:text-gray-400">
            Memverifikasi sesi kerja...
          </p>
        </div>
      </div>
    );
  }

  if (!token || !isRouteAllowed) {
    return null;
  }

  const mainContentMargin = isMobileOpen
    ? "ms-0"
    : isExpanded || isHovered
    ? "lg:ms-72.5"
    : "lg:ms-22.5";

  return (
    <SimulatorProvider>
      <div className="min-h-screen xl:flex">
        <AppSidebar />
        <Backdrop />
        <div
          className={`flex-1 min-w-0 overflow-x-clip transition-all duration-300 ease-in-out ${mainContentMargin}`}
        >
          <AppHeader />
          <div className="mx-auto max-w-(--breakpoint-2xl) w-full max-w-full p-4 md:p-6">
            {children}
          </div>
        </div>
      </div>
    </SimulatorProvider>
  );
}
