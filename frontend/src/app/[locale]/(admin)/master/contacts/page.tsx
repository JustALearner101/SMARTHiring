"use client";

import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import FormField from "@/components/form/FormField";
import InputField from "@/components/form/input/InputField";
import Select from "@/components/form/Select";
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
import { initialInterviewers } from "@/data/mockMasterData";
import {
  InfoIcon,
  PencilIcon,
  PlusIcon,
  TrashBinIcon,
} from "@/icons";
import { Department, InterviewerContact, Timezone } from "@/types/master";
import { useMemo, useState } from "react";

export default function ContactsPage() {
  const [contacts, setContacts] = useState<InterviewerContact[]>(initialInterviewers);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDept, setSelectedDept] = useState<string>("ALL");
  const [selectedTimezone, setSelectedTimezone] = useState<string>("ALL");

  // Modals
  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [activeContact, setActiveContact] = useState<InterviewerContact | null>(null);

  // Form State
  const [formData, setFormData] = useState({
    employee_id: "",
    name: "",
    email: "",
    phone: "",
    department: "Engineering" as Department,
    role: "",
    timezone: "WIB" as Timezone,
    working_hours: "09:00 - 17:00",
  });

  // Filtered List
  const filteredContacts = useMemo(() => {
    return contacts.filter((item) => {
      const q = searchQuery.toLowerCase();
      const matchesSearch =
        item.name.toLowerCase().includes(q) ||
        item.employee_id.toLowerCase().includes(q) ||
        item.email.toLowerCase().includes(q) ||
        item.role.toLowerCase().includes(q);

      const matchesDept = selectedDept === "ALL" || item.department === selectedDept;
      const matchesTimezone = selectedTimezone === "ALL" || item.timezone === selectedTimezone;

      return matchesSearch && matchesDept && matchesTimezone;
    });
  }, [contacts, searchQuery, selectedDept, selectedTimezone]);

  // Open Add Modal
  const handleOpenAdd = () => {
    setActiveContact(null);
    setFormData({
      employee_id: `EMP-${Date.now().toString().slice(-4)}`,
      name: "",
      email: "",
      phone: "+628",
      department: "Engineering",
      role: "",
      timezone: "WIB",
      working_hours: "09:00 - 17:00",
    });
    setIsFormModalOpen(true);
  };

  // Open Edit Modal
  const handleOpenEdit = (item: InterviewerContact) => {
    setActiveContact(item);
    setFormData({
      employee_id: item.employee_id,
      name: item.name,
      email: item.email,
      phone: item.phone,
      department: item.department,
      role: item.role,
      timezone: item.timezone,
      working_hours: item.working_hours,
    });
    setIsFormModalOpen(true);
  };

  // Unified Save Contact (Add or Edit)
  const handleSaveContact = () => {
    if (!formData.name.trim() || !formData.email.trim() || !formData.role.trim()) {
      alert("Please fill in the interviewer's name, email, and position.");
      return;
    }

    if (activeContact) {
      setContacts(
        contacts.map((c) =>
          c.id === activeContact.id
            ? {
                ...c,
                name: formData.name,
                email: formData.email,
                phone: formData.phone,
                department: formData.department,
                role: formData.role,
                timezone: formData.timezone,
                working_hours: formData.working_hours,
              }
            : c
        )
      );
    } else {
      const initials = formData.name
        .split(" ")
        .map((n) => n[0])
        .slice(0, 2)
        .join("")
        .toUpperCase();

      const newContact: InterviewerContact = {
        id: `int-${Date.now()}`,
        employee_id: formData.employee_id,
        name: formData.name,
        email: formData.email,
        phone: formData.phone,
        department: formData.department,
        role: formData.role,
        timezone: formData.timezone,
        working_hours: formData.working_hours,
        avatar_initials: initials || "IN",
      };

      setContacts([...contacts, newContact]);
    }

    setIsFormModalOpen(false);
  };

  // Confirm Delete
  const handleConfirmDelete = () => {
    if (!activeContact) return;
    setContacts(contacts.filter((c) => c.id !== activeContact.id));
    setIsDeleteModalOpen(false);
  };

  // Department Badge Colors
  const renderDeptBadge = (dept: Department) => {
    switch (dept) {
      case "Engineering":
        return <Badge color="primary" size="sm">Engineering</Badge>;
      case "Product":
        return <Badge color="warning" size="sm">Product</Badge>;
      case "Finance":
        return <Badge color="success" size="sm">Finance</Badge>;
      case "People Operations":
        return <Badge color="info" size="sm">People Ops</Badge>;
      default:
        return <Badge color="light" size="sm">Operations</Badge>;
    }
  };

  return (
    <div>
      <PageBreadcrumb pageTitle="Interviewer Directory" />

      {/* Disambiguation Test Case Alert Banner */}
      {/* <div className="mb-5 rounded-2xl border border-brand-200 bg-brand-50/70 p-4.5 dark:border-brand-500/20 dark:bg-brand-500/10">
        <div className="flex items-start gap-3.5">
          <div className="rounded-xl bg-brand-500 p-2 text-white shrink-0 shadow-theme-xs">
            <InfoIcon className="w-6 h-6" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-brand-900 dark:text-brand-300">
              Hackathon Committee Test Case: &quot;Two Mr. Budis&quot; Disambiguation Scenario
            </h4>
            <p className="mt-1 text-xs text-brand-700 dark:text-brand-400 leading-relaxed">
              This table contains data for two interviewers named <strong>Budi</strong> with different departments and timezones:
              <br />
              1. <strong>Budi Santoso</strong> — <em>VP of Engineering</em> (Jakarta - WIB).
              <br />
              2. <strong>Budi Raharjo</strong> — <em>Head of Finance</em> (Bali - WITA).
              <br />
              When HR gives a natural language command: <em>&quot;Schedule an interview with Mr. Budi&quot;</em>, the AI Orchestrator system will trigger <strong>The LIMITS Pillar (Disambiguation Gate)</strong> to request human clarification.
            </p>
          </div>
        </div>
      </div> */}

      {/* Main Container */}
      <div className="rounded-2xl border border-gray-200 bg-white p-5 xl:p-6 dark:border-gray-800 dark:bg-gray-900 shadow-theme-xs">
        {/* Header Actions */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between pb-5 border-b border-gray-100 dark:border-gray-800">
          <div>
            <h3 className="text-theme-xl font-semibold text-gray-800 dark:text-white/90">
              Interviewer & Internal Contacts
            </h3>
            <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
              List of hiring managers referenced by the AI Retriever to check for available calendar slots and send email invitations.
            </p>
          </div>
          <Button
            variant="primary"
            size="md"
            startIcon={<PlusIcon className="w-3 h-3" />}
            onClick={handleOpenAdd}
          >
            Add Interviewer
          </Button>
        </div>

        {/* Filter Controls Bar */}
        <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-12">
          {/* Search Box */}
          <div className="sm:col-span-6">
            <InputField
              placeholder="Search nama"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          {/* Department Filter */}
          <div className="sm:col-span-3">
            <Select
              options={[
                { value: "ALL", label: "All Department" },
                { value: "Engineering", label: "Engineering" },
                { value: "Product", label: "Product" },
                { value: "Finance", label: "Finance" },
                { value: "People Operations", label: "People Operations" },
                { value: "Operations", label: "Operations" },
              ]}
              value={selectedDept}
              onChange={(e) => setSelectedDept(e.target.value)}
            />
          </div>

          {/* Timezone Filter */}
          <div className="sm:col-span-3">
            <Select
              options={[
                { value: "ALL", label: "All Timezone" },
                { value: "WIB", label: "WIB (UTC+7)" },
                { value: "WITA", label: "WITA (UTC+8)" },
                { value: "WIT", label: "WIT (UTC+9)" },
              ]}
              value={selectedTimezone}
              onChange={(e) => setSelectedTimezone(e.target.value)}
            />
          </div>
        </div>

        {/* Contacts Table */}
        <div className="mt-5 overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-800">
          <Table>
            <TableHeader className="bg-gray-50 dark:bg-gray-800/60 border-b border-gray-200 dark:border-gray-800">
              <TableRow>
                <TableCell isHeader className="ps-4 pe-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300">
                  Interviewer / User
                </TableCell>
                <TableCell isHeader className="px-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300">
                  Department & Position
                </TableCell>
                <TableCell isHeader className="px-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300">
                  Timezone
                </TableCell>
                <TableCell isHeader className="px-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300">
                  Working Hours
                </TableCell>
                <TableCell isHeader className="px-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300">
                  Contact
                </TableCell>
                <TableCell isHeader className="pe-5 ps-3 py-3 text-end text-xs font-semibold text-gray-600 dark:text-gray-300">
                  Actions
                </TableCell>
              </TableRow>
            </TableHeader>
            <TableBody className="divide-y divide-gray-100 dark:divide-gray-800">
              {filteredContacts.length === 0 ? (
                <TableRow>
                  <TableCell className="py-8 text-center text-xs text-gray-400">
                    No contacts match the search filter.
                  </TableCell>
                </TableRow>
              ) : (
                filteredContacts.map((item) => (
                  <TableRow key={item.id} className="hover:bg-gray-50/70 dark:hover:bg-white/[0.02] transition-colors">
                    {/* Interviewer Info with Avatar */}
                    <TableCell className="ps-4 pe-3 py-3.5">
                      <div className="flex items-center gap-3">
                        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-50 font-semibold text-xs text-brand-600 dark:bg-brand-500/15 dark:text-brand-400 border border-brand-200 dark:border-brand-500/20">
                          {item.avatar_initials}
                        </div>
                        <div className="flex flex-col">
                          <span className="font-semibold text-sm text-gray-900 dark:text-white/90">
                            {item.name}
                          </span>
                          <span className="text-[11px] font-mono text-gray-400">
                            {item.employee_id}
                          </span>
                        </div>
                      </div>
                    </TableCell>

                    {/* Department & Role */}
                    <TableCell className="px-3 py-3.5">
                      <div className="flex flex-col gap-1 items-start">
                        {renderDeptBadge(item.department)}
                        <span className="text-xs text-gray-700 dark:text-gray-300 font-medium">
                          {item.role}
                        </span>
                      </div>
                    </TableCell>

                    {/* Timezone */}
                    <TableCell className="px-3 py-3.5">
                      <span className="inline-flex items-center rounded-md bg-gray-100 px-2 py-0.5 text-xs font-mono font-medium text-gray-700 dark:bg-gray-800 dark:text-gray-300">
                        {item.timezone}
                      </span>
                    </TableCell>

                    {/* Working Hours */}
                    <TableCell className="px-3 py-3.5 text-xs text-gray-600 dark:text-gray-400 font-mono">
                      {item.working_hours}
                    </TableCell>

                    {/* Contact Details */}
                    <TableCell className="px-3 py-3.5">
                      <div className="flex flex-col text-xs text-gray-500 dark:text-gray-400">
                        <span className="font-medium text-gray-700 dark:text-gray-300">{item.email}</span>
                        <span className="text-[11px]">{item.phone}</span>
                      </div>
                    </TableCell>

                    {/* Actions */}
                    <TableCell className="pe-5 ps-3 py-3.5 text-end whitespace-nowrap">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          type="button"
                          onClick={() => handleOpenEdit(item)}
                          className="h-8 w-8 inline-flex items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-600 shadow-theme-xs hover:border-brand-300 hover:bg-gray-50 hover:text-brand-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:border-brand-500/30 dark:hover:bg-gray-700/60 dark:hover:text-brand-400 transition-all"
                          title="Edit Kontak"
                        >
                          <PencilIcon className="w-5 h-5" />
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            setActiveContact(item);
                            setIsDeleteModalOpen(true);
                          }}
                          className="h-8 w-8 inline-flex items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-500 shadow-theme-xs hover:border-error-300 hover:bg-error-50 hover:text-error-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400 dark:hover:border-error-500/30 dark:hover:bg-error-500/15 dark:hover:text-error-400 transition-all"
                          title="Hapus Kontak"
                        >
                          <TrashBinIcon className="w-5 h-5" />
                        </button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Footer Summary */}
        <div className="mt-4 flex items-center justify-between text-xs text-gray-400">
          <span>Showing {filteredContacts.length} of {contacts.length} total interviewer</span>
          <span className="font-mono">API Contract: tblm_user</span>
        </div>
      </div>

      {/* Unified Interviewer Form Modal (Add / Edit) */}
      <Modal isOpen={isFormModalOpen} onClose={() => setIsFormModalOpen(false)} className="max-w-4xl m-4">
        <div className="p-10">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {activeContact
              ? `Edit Interviewer (${activeContact.employee_id})`
              : "Add New Interviewer"}
          </h3>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            {activeContact
              ? "Update data role, department, and timezone availability of interviewer."
              : "Register internal Hiring Manager or Lead who will interview candidates."}
          </p>

          <div className="mt-5 space-y-3.5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <FormField label="Full Name" required>
                <InputField
                  placeholder="e.g., Budi Santoso"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </FormField>

              <FormField label="Employee ID" required>
                <InputField
                  placeholder="EMP-ENG-001"
                  value={formData.employee_id}
                  disabled={!!activeContact}
                  onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
                />
              </FormField>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <FormField label="Company Email" required>
                <InputField
                  type="email"
                  placeholder="budi.santoso@company.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                />
              </FormField>

              <FormField label="Phone Number" required>
                <InputField
                  placeholder="+6281211112222"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                />
              </FormField>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <FormField label="Department" required>
                <Select
                  options={[
                    { value: "Engineering", label: "Engineering" },
                    { value: "Product", label: "Product" },
                    { value: "Finance", label: "Finance" },
                    { value: "People Operations", label: "People Operations" },
                    { value: "Operations", label: "Operations" },
                  ]}
                  value={formData.department}
                  onChange={(e) => setFormData({ ...formData, department: e.target.value as Department })}
                />
              </FormField>

              <FormField label="Position" required>
                <InputField
                  placeholder="e.g., VP of Engineering"
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                />
              </FormField>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <FormField label="Timezone" required>
                <Select
                  options={[
                    { value: "WIB", label: "WIB (UTC+7, Jakarta)" },
                    { value: "WITA", label: "WITA (UTC+8, Bali/Makassar)" },
                    { value: "WIT", label: "WIT (UTC+9, Jayapura)" },
                  ]}
                  value={formData.timezone}
                  onChange={(e) => setFormData({ ...formData, timezone: e.target.value as Timezone })}
                />
              </FormField>

              <FormField label="Working Hours" required>
                <InputField
                  placeholder="09:00 - 17:00"
                  value={formData.working_hours}
                  onChange={(e) => setFormData({ ...formData, working_hours: e.target.value })}
                />
              </FormField>
            </div>
          </div>

          <div className="mt-6 flex justify-end gap-2.5 pt-3 border-t border-gray-100 dark:border-gray-800">
            <Button variant="outline" onClick={() => setIsFormModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleSaveContact}>
              {activeContact ? "Update" : "Save"}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal isOpen={isDeleteModalOpen} onClose={() => setIsDeleteModalOpen(false)}>
        <div className="p-6 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-error-50 text-error-500 dark:bg-error-500/10 mb-3">
            <TrashBinIcon className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-gray-900 dark:text-white">
            Delete Interviewer?
          </h3>
          <p className="mt-1.5 text-xs text-gray-500 dark:text-gray-400">
            Are you sure you want to delete{" "}
            <span className="font-semibold text-gray-800 dark:text-gray-200">
              {activeContact?.name}
            </span>{" "}
            ({activeContact?.role})?
          </p>

          <div className="mt-6 flex justify-center gap-2.5">
            <Button variant="outline" onClick={() => setIsDeleteModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleConfirmDelete}>
              Delete
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
