"use client";

import React, { useState } from "react";
import { PaperPlaneIcon, FileIcon } from "@/icons";

interface WhatsAppInputProps {
  onSendMessage: (text: string) => void;
  disabled?: boolean;
}

export default function WhatsAppInput({
  onSendMessage,
  disabled = false,
}: WhatsAppInputProps) {
  const [input, setInput] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || disabled) return;
    onSendMessage(input.trim());
    setInput("");
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="flex items-center gap-2 border-t border-gray-200 bg-white p-3 dark:border-gray-800 dark:bg-gray-900"
    >
      <button
        type="button"
        className="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-800 dark:hover:text-gray-300"
        title="Attach file (disabled in simulator)"
      >
        <FileIcon/>
      </button>

      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder={
          disabled
            ? "Waiting for SmartHiring AI response..."
            : "Type candidate message (e.g. 'Bisa ganti ke jam 2 siang?')..."
        }
        disabled={disabled}
        className="flex-1 rounded-xl border border-gray-300 bg-gray-50 px-4 py-2.5 text-sm text-gray-800 placeholder-gray-400 focus:border-emerald-500 focus:bg-white focus:outline-hidden focus:ring-1 focus:ring-emerald-500 dark:border-gray-700 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500 dark:focus:border-emerald-500"
      />

      <button
        type="submit"
        disabled={!input.trim() || disabled}
        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-600 text-white shadow-xs transition-colors hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed"
        title="Send reply"
      >
        <PaperPlaneIcon/>
      </button>
    </form>
  );
}
