"use client";

import { useRouter } from "@/i18n/navigation";
import { cn } from "@/utils";
import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Dropdown } from "../ui/dropdown/Dropdown";
import {
  AlertIcon,
  CheckCircleIcon,
  CheckLineIcon,
  CloseLineIcon,
  DocsIcon,
  LockIcon,
  TrashBinIcon,
} from "@/icons";
import { orchestrationService, simulatorService } from "@/services";

export type NotificationCategory = "APPROVAL" | "SECURITY" | "TRIAGE" | "INTERVIEW";

export interface SystemNotification {
  id: string;
  title: string;
  message: string;
  category: NotificationCategory;
  timestamp: string;
  isRead: boolean;
  link: string;
}

const INITIAL_NOTIFICATIONS: SystemNotification[] = [
  {
    id: "notif-appr-01",
    title: "Action Plan Awaiting Approval",
    message: "AI Orchestrator drafted interview plan for Rina Kusuma (Technical Round with Budi Santoso).",
    category: "APPROVAL",
    timestamp: "Just now",
    isRead: false,
    link: "/",
  },
  {
    id: "notif-sec-01",
    title: "Prompt Injection Blocked",
    message: "AI Guardrail detected & sanitized suspicious prompt injection from candidate WhatsApp channel.",
    category: "SECURITY",
    timestamp: "12 min ago",
    isRead: false,
    link: "/audit/guardrail",
  },
  {
    id: "notif-tri-01",
    title: "Candidate Reschedule Request",
    message: "Rina Kusuma requested Friday noon slot. AI detected Friday prayer blackout and proposed 14:00 WIB.",
    category: "TRIAGE",
    timestamp: "35 min ago",
    isRead: false,
    link: "/simulator/whatsapp",
  },
  {
    id: "notif-eval-01",
    title: "Interview Rubric Summary Ready",
    message: "AI Copilot extracted competency evidence and score predictions for Technical Interview.",
    category: "INTERVIEW",
    timestamp: "1 hr ago",
    isRead: true,
    link: "/interviews/review",
  },
];

export default function NotificationDropdown() {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [activeFilter, setActiveFilter] = useState<"ALL" | "APPROVAL" | "SECURITY">("ALL");
  const [deletedIds, setDeletedIds] = useState<Set<string>>(new Set());
  const [readIds, setReadIds] = useState<Set<string>>(new Set());
  const [isAllCleared, setIsAllCleared] = useState(false);

  // Cached query with TanStack Query: Stale time 60s, so repeated renders/refresh do not refetch!
  const { data: dynamicItems = [] } = useQuery({
    queryKey: ["notifications", "live"],
    queryFn: async () => {
      const [plan, simNotifs] = await Promise.allSettled([
        orchestrationService.getCurrentActionPlan(),
        simulatorService.listSimulatorNotifications(),
      ]);

      const items: SystemNotification[] = [];

      // Check if there is an active plan waiting for HR approval
      if (
        plan.status === "fulfilled" &&
        plan.value &&
        plan.value.status === "PENDING_APPROVAL"
      ) {
        const planMsg = plan.value.candidate_name
          ? `Action plan for ${plan.value.candidate_name} (${plan.value.candidate_position || "Interview"}) is awaiting your sign-off.`
          : `Action plan #${plan.value.id} is awaiting your sign-off before sending.`;

        items.push({
          id: `plan-${plan.value.id}`,
          title: "Human Approval Required",
          message: planMsg,
          category: "APPROVAL",
          timestamp: "Live",
          isRead: false,
          link: "/",
        });
      }

      // Ingest simulator notifications
      if (simNotifs.status === "fulfilled" && Array.isArray(simNotifs.value)) {
        for (const item of simNotifs.value) {
          items.push({
            id: item.id,
            title: item.title,
            message: item.message,
            category: item.type === "guardrail_blocked" ? "SECURITY" : "TRIAGE",
            timestamp: "Recent",
            isRead: false,
            link: item.action_url || "/simulator/whatsapp",
          });
        }
      }

      return items;
    },
    staleTime: 60 * 1000,
  });

  // Pure derived state — avoids cascading setState renders
  const notifications = useMemo<SystemNotification[]>(() => {
    if (isAllCleared) return [];

    const existingIds = new Set(INITIAL_NOTIFICATIONS.map((n) => n.id));
    const freshDynamic = dynamicItems.filter((d) => !existingIds.has(d.id));
    const merged = [...freshDynamic, ...INITIAL_NOTIFICATIONS];

    return merged
      .filter((item) => !deletedIds.has(item.id))
      .map((item) => (readIds.has(item.id) ? { ...item, isRead: true } : item));
  }, [dynamicItems, deletedIds, readIds, isAllCleared]);

  const unreadCount = useMemo(() => {
    return notifications.filter((n) => !n.isRead).length;
  }, [notifications]);

  const filteredNotifications = useMemo(() => {
    if (activeFilter === "ALL") return notifications;
    return notifications.filter((n) => n.category === activeFilter);
  }, [notifications, activeFilter]);

  const handleMarkAllAsRead = () => {
    setReadIds(new Set(notifications.map((n) => n.id)));
  };

  const handleClearAll = () => {
    setIsAllCleared(true);
  };

  const handleDeleteNotification = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    setDeletedIds((prev) => new Set([...prev, id]));
  };

  const handleItemClick = (item: SystemNotification) => {
    setReadIds((prev) => new Set([...prev, item.id]));
    setIsOpen(false);
    router.push(item.link);
  };

  const renderCategoryBadge = (category: NotificationCategory) => {
    switch (category) {
      case "APPROVAL":
        return (
          <span className="inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[10px] font-semibold bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-400 border border-brand-200 dark:border-brand-500/20">
            <CheckCircleIcon/> Approval
          </span>
        );
      case "SECURITY":
        return (
          <span className="inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[10px] font-semibold bg-error-50 text-error-600 dark:bg-error-500/15 dark:text-error-400 border border-error-200 dark:border-error-500/20">
            <LockIcon/> Security
          </span>
        );
      case "TRIAGE":
        return (
          <span className="inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[10px] font-semibold bg-warning-50 text-warning-600 dark:bg-warning-500/15 dark:text-warning-400 border border-warning-200 dark:border-warning-500/20">
            <AlertIcon/> Triage
          </span>
        );
      case "INTERVIEW":
        return (
          <span className="inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[10px] font-semibold bg-success-50 text-success-600 dark:bg-success-500/15 dark:text-success-400 border border-success-200 dark:border-success-500/20">
            <DocsIcon/> Evaluation
          </span>
        );
    }
  };

  return (
    <div className="relative">
      {/* Bell Button */}
      <button
        type="button"
        className="dropdown-toggle relative flex h-11 w-11 items-center justify-center rounded-full border border-gray-200 bg-white text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-white"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-label="Notifications"
      >
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 z-10 flex h-5 min-w-[20px] items-center justify-center rounded-full bg-error-500 px-1 text-[11px] font-bold text-white shadow-sm animate-in zoom-in">
            {unreadCount}
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-error-400 opacity-75" />
          </span>
        )}
        <svg
          className="fill-current"
          width="20"
          height="20"
          viewBox="0 0 20 20"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            fillRule="evenodd"
            clipRule="evenodd"
            d="M10.75 2.29248C10.75 1.87827 10.4143 1.54248 10 1.54248C9.58583 1.54248 9.25004 1.87827 9.25004 2.29248V2.83613C6.08266 3.20733 3.62504 5.9004 3.62504 9.16748V14.4591H3.33337C2.91916 14.4591 2.58337 14.7949 2.58337 15.2091C2.58337 15.6234 2.91916 15.9591 3.33337 15.9591H4.37504H15.625H16.6667C17.0809 15.9591 17.4167 15.6234 17.4167 15.2091C17.4167 14.7949 17.0809 14.4591 16.6667 14.4591H16.375V9.16748C16.375 5.9004 13.9174 3.20733 10.75 2.83613V2.29248ZM14.875 14.4591V9.16748C14.875 6.47509 12.6924 4.29248 10 4.29248C7.30765 4.29248 5.12504 6.47509 5.12504 9.16748V14.4591H14.875ZM8.00004 17.7085C8.00004 18.1228 8.33583 18.4585 8.75004 18.4585H11.25C11.6643 18.4585 12 18.1228 12 17.7085C12 17.2943 11.6643 16.9585 11.25 16.9585H8.75004C8.33583 16.9585 8.00004 17.2943 8.00004 17.7085Z"
            fill="currentColor"
          />
        </svg>
      </button>

      {/* Notification Dropdown Panel */}
      <Dropdown
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        className="absolute -left-16 sm:left-auto sm:right-0 mt-3 flex h-[460px] w-[340px] sm:w-[410px] flex-col rounded-2xl border border-gray-200 bg-white p-4 shadow-theme-lg dark:border-gray-800 dark:bg-gray-900 z-99999"
      >
        {/* Header Bar */}
        <div className="flex items-center justify-between border-b border-gray-100 pb-3 dark:border-gray-800">
          <div className="flex items-center gap-2">
            <h5 className="text-base font-semibold text-gray-800 dark:text-white">
              Notifications
            </h5>
            {unreadCount > 0 && (
              <span className="rounded-full bg-brand-50 px-2 py-0.5 text-xs font-semibold text-brand-600 dark:bg-brand-500/15 dark:text-brand-400">
                {unreadCount} new
              </span>
            )}
          </div>
          <div className="flex items-center gap-3">
            {unreadCount > 0 && (
              <button
                type="button"
                onClick={handleMarkAllAsRead}
                className="text-xs font-medium text-brand-500 hover:text-brand-600 dark:text-brand-400 hover:underline flex items-center gap-1"
                title="Mark all notifications as read"
              >
                <CheckLineIcon /> Mark all read
              </button>
            )}
            {notifications.length > 0 && (
              <button
                type="button"
                onClick={handleClearAll}
                className="text-xs font-medium text-error-500 hover:text-error-600 dark:text-error-400 hover:underline flex items-center gap-1"
                title="Clear all notifications"
              >
                <TrashBinIcon /> Clear all
              </button>
            )}
          </div>
        </div>

        {/* Filter Chips */}
        <div className="mt-2.5 flex items-center gap-1.5 border-b border-gray-100 pb-2.5 dark:border-gray-800">
          <button
            type="button"
            onClick={() => setActiveFilter("ALL")}
            className={cn(
              "rounded-lg px-2.5 py-1 text-xs font-medium transition-colors",
              activeFilter === "ALL"
                ? "bg-brand-500 text-white"
                : "text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
            )}
          >
            All ({notifications.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveFilter("APPROVAL")}
            className={cn(
              "rounded-lg px-2.5 py-1 text-xs font-medium transition-colors",
              activeFilter === "APPROVAL"
                ? "bg-brand-500 text-white"
                : "text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
            )}
          >
            Approvals
          </button>
          <button
            type="button"
            onClick={() => setActiveFilter("SECURITY")}
            className={cn(
              "rounded-lg px-2.5 py-1 text-xs font-medium transition-colors",
              activeFilter === "SECURITY"
                ? "bg-brand-500 text-white"
                : "text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
            )}
          >
            Security
          </button>
        </div>

        {/* Notification Items List */}
        <div className="flex-1 overflow-y-auto space-y-2 py-2 pr-1 custom-scrollbar">
          {notifications.length === 0 ? (
            <div className="py-16 flex flex-col items-center justify-center text-center">
              <span className="rounded-full bg-gray-100 p-3 text-gray-400 dark:bg-gray-800 dark:text-gray-500 mb-2">
                <CheckCircleIcon />
              </span>
              <p className="text-xs font-medium text-gray-600 dark:text-gray-300">
                No notifications
              </p>
              <p className="text-[11px] text-gray-400 mt-0.5">
                You&apos;re all caught up!
              </p>
            </div>
          ) : filteredNotifications.length === 0 ? (
            <div className="py-12 text-center text-xs text-gray-400">
              No notifications in this category.
            </div>
          ) : (
            filteredNotifications.map((item) => (
              <div
                key={item.id}
                onClick={() => handleItemClick(item)}
                className={cn(
                  "cursor-pointer rounded-xl p-3 transition-all border text-start group relative",
                  item.isRead
                    ? "border-transparent bg-white hover:bg-gray-50 dark:bg-gray-900 dark:hover:bg-gray-800/50"
                    : "border-brand-100 bg-brand-50/30 hover:bg-brand-50/60 dark:border-brand-500/20 dark:bg-brand-500/5 dark:hover:bg-brand-500/10"
                )}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    {renderCategoryBadge(item.category)}
                    <span className="text-xs font-semibold text-gray-900 dark:text-white">
                      {item.title}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    {!item.isRead && (
                      <span className="h-2 w-2 shrink-0 rounded-full bg-brand-500" />
                    )}
                    <button
                      type="button"
                      onClick={(e) => handleDeleteNotification(e, item.id)}
                      className="p-1 rounded-md text-gray-400 hover:text-error-500 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                      title="Delete notification"
                      aria-label="Delete notification"
                    >
                      <CloseLineIcon/>
                    </button>
                  </div>
                </div>

                <p className="mt-1 text-xs text-gray-600 dark:text-gray-300 line-clamp-2 leading-relaxed">
                  {item.message}
                </p>

                <div className="mt-2 flex items-center justify-between text-[11px] text-gray-400">
                  <span>{item.timestamp}</span>
                  <span className="text-brand-500 dark:text-brand-400 font-medium hover:underline">
                    View Details →
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </Dropdown>
    </div>
  );
}
