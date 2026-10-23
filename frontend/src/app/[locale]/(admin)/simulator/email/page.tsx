"use client";

import React, { useState } from "react";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import EmailSidebar from "@/components/simulator/email/EmailSidebar";
import EmailList from "@/components/simulator/email/EmailList";
import EmailViewer from "@/components/simulator/email/EmailViewer";
import { useSimulator } from "@/context/SimulatorContext";
import { MailIcon, CheckCircleIcon, UserIcon } from "@/icons";

export default function InterviewerEmailSimulatorPage() {
  const {
    emails,
    activeEmailId,
    selectedInterviewer,
    setActiveEmailId,
    setSelectedInterviewer,
    sendEmailReply,
    resetSimulator,
  } = useSimulator();

  const [currentFolder, setCurrentFolder] = useState<"inbox" | "sent" | "starred">("inbox");

  // Filter emails based on active folder
  const filteredEmails = emails.filter((mail) => {
    if (currentFolder === "sent") {
      return mail.folder === "sent";
    }
    return mail.folder === "inbox";
  });

  const activeEmail = emails.find((m) => m.id === activeEmailId) || filteredEmails[0];

  const inboxCount = emails.filter((m) => m.folder === "inbox" && !m.is_read).length;
  const sentCount = emails.filter((m) => m.folder === "sent").length;

  return (
    <div>
      <PageBreadcrumb pageTitle="Interviewer Email Simulator" />

      {/* Overview Banner */}
      <div className="mb-4 rounded-xl border border-gray-200 bg-white p-4 shadow-2xs dark:border-gray-800 dark:bg-gray-900">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-400">
              <MailIcon/>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                <span>Corporate Webmail Simulator (Hiring Manager Inbox)</span>
                <span className="rounded bg-brand-50 px-2 py-0.5 text-[10px] font-bold text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">
                  INTERNAL CHANNEL
                </span>
              </h3>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Simulates official interview notifications, reschedule verifications, and HM calendar sync.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-lg bg-gray-100 px-3 py-1.5 text-xs font-medium text-gray-700 dark:bg-gray-800 dark:text-gray-300">
              <UserIcon className="text-brand-500" />
              <span>Active: {selectedInterviewer}</span>
            </span>
            <span className="inline-flex items-center gap-1 rounded-md bg-success-50 px-2.5 py-1 text-xs font-medium text-success-700 dark:bg-success-500/15 dark:text-success-300">
              <CheckCircleIcon/>
              Sync Active
            </span>
          </div>
        </div>
      </div>

      {/* Webmail Shell (3-Column Layout) */}
      <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-gray-900 flex flex-col md:flex-row min-h-[650px]">
        {/* Left: Folders & Account Switcher */}
        <EmailSidebar
          currentFolder={currentFolder}
          onSelectFolder={setCurrentFolder}
          selectedInterviewer={selectedInterviewer}
          onSelectInterviewer={setSelectedInterviewer}
          inboxCount={inboxCount}
          sentCount={sentCount}
          onReset={resetSimulator}
        />

        {/* Middle: Email List */}
        <EmailList
          emails={filteredEmails}
          activeEmailId={activeEmail?.id || ""}
          onSelectEmail={setActiveEmailId}
        />

        {/* Right: Email Viewer & Reply */}
        <EmailViewer
          email={activeEmail}
          onSendReply={sendEmailReply}
        />
      </div>
    </div>
  );
}
