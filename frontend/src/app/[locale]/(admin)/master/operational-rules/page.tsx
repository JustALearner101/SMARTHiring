"use client";

import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import FormField from "@/components/form/FormField";
import InputField from "@/components/form/input/InputField";
import Badge from "@/components/ui/badge/Badge";
import Button from "@/components/ui/button/Button";
import { Modal } from "@/components/ui/modal";
import {
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  initialNationalHolidays,
  initialOperationalPolicy,
} from "@/data/mockMasterData";
import {
  CheckCircleIcon,
  PlusIcon,
  TrashBinIcon,
} from "@/icons";
import { NationalHoliday, OperationalPolicy } from "@/types/master";
import { useState } from "react";

export default function OperationalRulesPage() {
  const [policy, setPolicy] = useState<OperationalPolicy>(initialOperationalPolicy);
  const [holidays, setHolidays] = useState<NationalHoliday[]>(initialNationalHolidays);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Add Holiday Modal
  const [isAddHolidayOpen, setIsAddHolidayOpen] = useState(false);
  const [newHolidayDate, setNewHolidayDate] = useState("");
  const [newHolidayName, setNewHolidayName] = useState("");
  const [newHolidayJointLeave, setNewHolidayJointLeave] = useState(false);

  // Save Policy Handler
  const handleSavePolicy = () => {
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 3000);
  };

  // Add Holiday Handler
  const handleAddHoliday = () => {
    if (!newHolidayDate || !newHolidayName.trim()) {
      alert("Harap isi tanggal dan nama hari libur.");
      return;
    }

    const item: NationalHoliday = {
      id: `hol-${Date.now()}`,
      date: newHolidayDate,
      name: newHolidayName,
      is_joint_leave: newHolidayJointLeave,
    };

    setHolidays([...holidays, item].sort((a, b) => a.date.localeCompare(b.date)));
    setNewHolidayDate("");
    setNewHolidayName("");
    setNewHolidayJointLeave(false);
    setIsAddHolidayOpen(false);
  };

  // Delete Holiday Handler
  const handleDeleteHoliday = (id: string) => {
    setHolidays(holidays.filter((h) => h.id !== id));
  };

  return (
    <div>
      <PageBreadcrumb pageTitle="Operational Rules & Calendar" />

      {/* Success Notification Alert */}
      {saveSuccess && (
        <div className="mb-5 flex items-center gap-3 rounded-xl border border-success-200 bg-success-50 p-4 text-xs font-medium text-success-800 dark:border-success-500/20 dark:bg-success-500/15 dark:text-success-300 animate-in fade-in">
          <CheckCircleIcon className="w-5 h-5 text-success-500 shrink-0" />
          <span>The operational rules were successfully cached in the AI Orchestrator</span>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Left Column: Work Policy Settings */}
        <div className="lg:col-span-5 space-y-6">
          <div className="rounded-2xl border border-gray-200 bg-white p-5 xl:p-6 dark:border-gray-800 dark:bg-gray-900 shadow-theme-xs">
            <div className="border-b border-gray-100 pb-4 dark:border-gray-800">
              <h3 className="text-theme-xl font-semibold text-gray-800 dark:text-white/90">
                Rules on Working Hours and Worship
              </h3>
              <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
                AI is prohibited from creating schedules outside operational hours or during Friday prayers.
              </p>
            </div>

            <div className="mt-5 space-y-4">
              {/* Working Hours */}
              <div className="grid grid-cols-2 gap-3">
                <FormField label="Work Start Time">
                  <InputField
                    type="time"
                    value={policy.work_start_time}
                    onChange={(e) => setPolicy({ ...policy, work_start_time: e.target.value })}
                  />
                </FormField>
                <FormField label="Work End Time">
                  <InputField
                    type="time"
                    value={policy.work_end_time}
                    onChange={(e) => setPolicy({ ...policy, work_end_time: e.target.value })}
                  />
                </FormField>
              </div>

              {/* Friday Prayer Block */}
              <div className="rounded-xl border border-gray-200 bg-gray-50/70 p-4 dark:border-gray-800 dark:bg-gray-800/40">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-800 dark:text-white/90">
                    Friday Prayer Block (Mandatory)
                  </span>
                  <Badge color="error" size="sm">Auto Block</Badge>
                </div>
                <div className="grid grid-cols-2 gap-3 mt-3">
                  <FormField label="Start (WIB)">
                    <InputField
                      type="time"
                      value={policy.friday_prayer_start}
                      onChange={(e) => setPolicy({ ...policy, friday_prayer_start: e.target.value })}
                    />
                  </FormField>
                  <FormField label="End (WIB)">
                    <InputField
                      type="time"
                      value={policy.friday_prayer_end}
                      onChange={(e) => setPolicy({ ...policy, friday_prayer_end: e.target.value })}
                    />
                  </FormField>
                </div>
                <div className="mt-2 text-[11px] text-gray-400 leading-relaxed">
                  • <strong>WITA</strong>: automatically converted to 12:30 – 14:00.<br />
                  • <strong>WIT</strong>: automatically converted to 13:30 – 15:00.
                </div>
              </div>

              {/* Triage Limits */}
              <div className="grid grid-cols-2 gap-3">
                <FormField label="Maximum Number of Triage Rounds" hint="LIMITS Pillar (Escalate to HR if > 3)">
                  <InputField
                    type="number"
                    min={1}
                    max={5}
                    value={policy.max_negotiation_rounds}
                    onChange={(e) => setPolicy({ ...policy, max_negotiation_rounds: parseInt(e.target.value) || 3 })}
                  />
                </FormField>
                <FormField label="Buffer Time Between Sessions (Minutes)" hint="Rest time buffer">
                  <InputField
                    type="number"
                    min={0}
                    max={60}
                    step={5}
                    value={policy.buffer_minutes}
                    onChange={(e) => setPolicy({ ...policy, buffer_minutes: parseInt(e.target.value) || 15 })}
                  />
                </FormField>
              </div>

              {/* Guardrail Toggle */}
              <div className="flex items-center justify-between rounded-xl border border-gray-200 p-3.5 dark:border-gray-800">
                <div>
                  <div className="text-xs font-semibold text-gray-800 dark:text-white/90">
                    Prompt Injection Guardrail
                  </div>
                  <div className="text-[11px] text-gray-400">
                    Scan for malicious instructions in CV & WhatsApp messages
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={policy.injection_guardrail_enabled}
                  onChange={(e) => setPolicy({ ...policy, injection_guardrail_enabled: e.target.checked })}
                  className="h-4 w-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                />
              </div>

              <div className="pt-2">
                <Button variant="primary" className="w-full" onClick={handleSavePolicy}>
                  Save Operational Rules
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: National Holidays 2026 */}
        <div className="lg:col-span-7">
          <div className="rounded-2xl border border-gray-200 bg-white p-5 xl:p-6 dark:border-gray-800 dark:bg-gray-900 shadow-theme-xs">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-gray-100 pb-4 dark:border-gray-800">
              <div>
                <h3 className="text-theme-xl font-semibold text-gray-800 dark:text-white/90">
                  National Holidays (2026)
                </h3>
                <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
                  Official calendar. AI automatically blocks all interview slots on these dates.
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                startIcon={<PlusIcon className="w-3.5 h-3.5" />}
                onClick={() => setIsAddHolidayOpen(true)}
              >
                Add Holiday
              </Button>
            </div>

            {/* Holidays Table */}
            <div className="mt-5 overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-800">
              <Table>
                <TableHeader className="bg-gray-50 dark:bg-gray-800/60 border-b border-gray-200 dark:border-gray-800">
                  <TableRow>
                    <TableCell isHeader className="ps-4 pe-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300">
                      Date
                    </TableCell>
                    <TableCell isHeader className="px-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300">
                      Holiday Name
                    </TableCell>
                    <TableCell isHeader className="px-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300">
                      Type
                    </TableCell>
                    <TableCell isHeader className="pe-5 ps-3 py-3 text-end text-xs font-semibold text-gray-600 dark:text-gray-300">
                      Actions
                    </TableCell>
                  </TableRow>
                </TableHeader>
                <TableBody className="divide-y divide-gray-100 dark:divide-gray-800">
                  {holidays.map((h) => (
                    <TableRow key={h.id} className="hover:bg-gray-50/70 dark:hover:bg-white/[0.02] transition-colors">
                      <TableCell className="ps-4 pe-3 py-3 text-xs font-mono font-medium text-gray-800 dark:text-gray-200">
                        {h.date}
                      </TableCell>
                      <TableCell className="px-3 py-3 text-xs text-gray-700 dark:text-gray-300 font-medium">
                        {h.name}
                      </TableCell>
                      <TableCell className="px-3 py-3">
                        {h.is_joint_leave ? (
                          <Badge color="warning" size="sm">Cuti Bersama</Badge>
                        ) : (
                          <Badge color="error" size="sm">Libur Nasional</Badge>
                        )}
                      </TableCell>
                      <TableCell className="pe-5 ps-3 py-3 text-end whitespace-nowrap">
                        <button
                          type="button"
                          onClick={() => handleDeleteHoliday(h.id)}
                          className="h-8 w-8 inline-flex items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-500 shadow-theme-xs hover:border-error-300 hover:bg-error-50 hover:text-error-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400 dark:hover:border-error-500/30 dark:hover:bg-error-500/15 dark:hover:text-error-400 transition-all"
                          title="Delete Holiday"
                        >
                          <TrashBinIcon className="w-5 h-5" />
                        </button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            <div className="mt-4 flex items-center justify-between text-xs text-gray-400">
              <span>{holidays.length} holidays registered in AI calendar</span>
              <span className="font-mono">API Contract: tblm_holiday</span>
            </div>
          </div>
        </div>
      </div>

      {/* Add Holiday Modal */}
      <Modal isOpen={isAddHolidayOpen} onClose={() => setIsAddHolidayOpen(false)} className="max-w-2xl m-4">
        <div className="p-10">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Add New Holiday
          </h3>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Register holiday or joint leave so that AI does not schedule interviews on this date.
          </p>

          <div className="mt-5 space-y-3.5">
            <FormField label="Holiday Date" required>
              <InputField
                type="date"
                value={newHolidayDate}
                onChange={(e) => setNewHolidayDate(e.target.value)}
              />
            </FormField>

            <FormField label="Holiday Name" required>
              <InputField
                placeholder="e.g., Company Additional Joint Leave"
                value={newHolidayName}
                onChange={(e) => setNewHolidayName(e.target.value)}
              />
            </FormField>

            <div className="flex items-center gap-2 pt-1">
              <input
                type="checkbox"
                id="isJointLeave"
                checked={newHolidayJointLeave}
                onChange={(e) => setNewHolidayJointLeave(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500"
              />
              <label htmlFor="isJointLeave" className="text-xs text-gray-700 dark:text-gray-300 cursor-pointer">
                Mark as <strong>Joint Leave</strong>
              </label>
            </div>
          </div>

          <div className="mt-6 flex justify-end gap-2.5 pt-3 border-t border-gray-100 dark:border-gray-800">
            <Button variant="outline" onClick={() => setIsAddHolidayOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleAddHoliday}>
              Add to Calendar
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
