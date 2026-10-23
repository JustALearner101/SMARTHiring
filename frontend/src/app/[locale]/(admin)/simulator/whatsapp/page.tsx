"use client";

import React, { useRef, useEffect } from "react";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import WhatsAppHeader from "@/components/simulator/whatsapp/WhatsAppHeader";
import WhatsAppBubble from "@/components/simulator/whatsapp/WhatsAppBubble";
import WhatsAppQuickBar from "@/components/simulator/whatsapp/WhatsAppQuickBar";
import WhatsAppInput from "@/components/simulator/whatsapp/WhatsAppInput";
import GuardrailAlert from "@/components/simulator/common/GuardrailAlert";
import { useSimulator } from "@/context/SimulatorContext";
import { QuickReplyPreset } from "@/types/simulator";
import { ChatIcon, InfoIcon, LockIcon } from "@/icons";

export default function CandidateWhatsappSimulatorPage() {
  const {
    whatsappMessages,
    isBotTyping,
    activeNegotiationRound,
    lastGuardrailIncident,
    sendWhatsAppMessage,
    dismissGuardrailAlert,
    resetSimulator,
  } = useSimulator();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [whatsappMessages, isBotTyping]);

  const handleSelectPreset = (preset: QuickReplyPreset) => {
    sendWhatsAppMessage(preset.payload_text, preset.preset_type);
  };

  return (
    <div>
      <PageBreadcrumb pageTitle="Candidate WhatsApp Simulator" />

      {/* Security Guardrail Incident Alert Banner */}
      {lastGuardrailIncident && (
        <GuardrailAlert
          payload={lastGuardrailIncident.payload}
          reason={lastGuardrailIncident.reason}
          timestamp={lastGuardrailIncident.timestamp}
          onDismiss={dismissGuardrailAlert}
        />
      )}

      {/* Module Overview Banner */}
      <div className="mb-4 rounded-xl border border-gray-200 bg-white p-4 shadow-2xs dark:border-gray-800 dark:bg-gray-900">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-400">
              <ChatIcon/>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                <span>In-App WhatsApp Web Simulator</span>
                <span className="rounded bg-error-50 px-2 py-0.5 text-[10px] font-bold text-error-600 dark:bg-error-500/15 dark:text-error-400">
                  HIGH-IMPACT EXTERNAL CHANNEL
                </span>
              </h3>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Simulates real-time candidate interactions and inbound webhooks for the 90-second judge presentation.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <span className="inline-flex items-center gap-1 rounded-md bg-gray-100 px-2.5 py-1 font-mono text-[11px] text-gray-700 dark:bg-gray-800 dark:text-gray-300">
              <LockIcon className="text-emerald-500" />
              Guardrail Active
            </span>
            <span className="inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2.5 py-1 font-medium text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300">
              Webhook: Mock Active
            </span>
          </div>
        </div>
      </div>

      {/* WhatsApp Client Shell */}
      <div className="overflow-hidden rounded-2xl border border-gray-200 bg-[#efeae2] shadow-sm dark:border-gray-800 dark:bg-gray-950 flex flex-col h-[700px]">
        {/* WhatsApp Header */}
        <WhatsAppHeader
          candidateName="Rina Kusuma"
          phoneNumber="+62 812-3456-7890"
          position="Senior Frontend Developer"
          isBotTyping={isBotTyping}
          negotiationRound={activeNegotiationRound}
          onReset={resetSimulator}
        />

        {/* Message Stream Area */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-2 bg-[radial-gradient(#d1d5db_1px,transparent_1px)] dark:bg-[radial-gradient(#374151_1px,transparent_1px)] [background-size:16px_16px]">
          {/* Encryption / System Notice Badge */}
          <div className="mb-4 flex justify-center">
            <div className="flex items-center gap-1.5 rounded-lg bg-yellow-50 px-3 py-1.5 text-center text-[11px] text-yellow-800 shadow-2xs border border-yellow-200/80 dark:bg-yellow-950/40 dark:text-yellow-200 dark:border-yellow-800/40">
              <InfoIcon className="shrink-0" />
              <span>
                Messages and calls are end-to-end encrypted. AI autonomous actions require verified human approval.
              </span>
            </div>
          </div>

          {/* Messages */}
          {whatsappMessages.map((msg) => (
            <WhatsAppBubble key={msg.id} message={msg} />
          ))}

          {/* Typing Indicator */}
          {isBotTyping && (
            <div className="flex items-center gap-1.5 mr-auto rounded-2xl rounded-tl-none bg-white px-4 py-2 text-xs text-gray-500 shadow-xs border border-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:border-gray-700">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-bounce" />
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-bounce [animation-delay:0.2s]" />
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-bounce [animation-delay:0.4s]" />
              <span className="ml-1 text-[11px]">SmartHiring is evaluating schedule availability...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* 1-Click Quick Preset Chips */}
        <WhatsAppQuickBar
          onSelectPreset={handleSelectPreset}
          disabled={isBotTyping}
        />

        {/* Text Input Bar */}
        <WhatsAppInput
          onSendMessage={(text) => sendWhatsAppMessage(text)}
          disabled={isBotTyping}
        />
      </div>
    </div>
  );
}
