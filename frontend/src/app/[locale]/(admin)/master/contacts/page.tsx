"use client";

import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import FormField from "@/components/form/FormField";
import InputField from "@/components/form/input/InputField";
import Select from "@/components/form/Select";
import Badge from "@/components/ui/badge/Badge";
import Button from "@/components/ui/button/Button";
import { ConfirmationModal, Modal } from "@/components/ui/modal";
import {
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { EyeCloseIcon, EyeIcon, PencilIcon, PlusIcon, TrashBinIcon } from "@/icons";
import { masterService } from "@/services";
import type { UserRole } from "@/types/auth";
import { Department, InterviewerContact, Timezone } from "@/types/master";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

export default function ContactsPage() {
  const { role } = useAuth();
  const canManageContacts = role === "HR" || role === "ADMIN";
  const { showSuccess, showError } = useToast();
  const [isSaving, setIsSaving] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDept, setSelectedDept] = useState<string>("ALL");
  const [selectedTimezone, setSelectedTimezone] = useState<string>("ALL");

  // Modals
  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [isSaveConfirmOpen, setIsSaveConfirmOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [activeContact, setActiveContact] = useState<InterviewerContact | null>(null);

  // Form State (Includes System Role, Username, and Argon2 Password)
  const [formData, setFormData] = useState({
    employee_id: "",
    name: "",
    username: "",
    password: "",
    system_role: "INTERVIEWER" as UserRole,
    email: "",
    phone: "",
    department: "Engineering" as Department,
    role: "",
    timezone: "WIB" as Timezone,
    working_hours: "09:00 - 17:00",
  });

  const queryClient = useQueryClient();
  const { data: contactsData, isLoading } = useQuery({
    queryKey: ["contacts"],
    queryFn: () => masterService.listContacts(),
  });

  const contacts = useMemo(
    () => (Array.isArray(contactsData) ? contactsData : []),
    [contactsData]
  );

  // Filtered List
  const filteredContacts = useMemo(() => {
    return contacts.filter((item) => {
      const q = searchQuery.toLowerCase();
      const matchesSearch =
        item.name.toLowerCase().includes(q) ||
        item.employee_id.toLowerCase().includes(q) ||
        (item.username || "").toLowerCase().includes(q) ||
        item.email.toLowerCase().includes(q) ||
        item.role.toLowerCase().includes(q);

      const matchesDept = selectedDept === "ALL" || item.department === selectedDept;
      const matchesTimezone =
        selectedTimezone === "ALL" || item.timezone === selectedTimezone;

      return matchesSearch && matchesDept && matchesTimezone;
    });
  }, [contacts, searchQuery, selectedDept, selectedTimezone]);

  // Open Add Modal
  const handleOpenAdd = () => {
    setActiveContact(null);
    setShowPassword(false);
    setFormData({
      employee_id: `EMP-${Date.now().toString().slice(-4)}`,
      name: "",
      username: "",
      password: "",
      system_role: "INTERVIEWER",
      email: "",
      phone: "",
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
    setShowPassword(false);
    setFormData({
      employee_id: item.employee_id,
      name: item.name,
      username: item.username || "",
      password: "",
      system_role: item.system_role || "INTERVIEWER",
      email: item.email,
      phone: item.phone,
      department: item.department,
      role: item.role,
      timezone: item.timezone,
      working_hours: item.working_hours,
    });
    setIsFormModalOpen(true);
  };

  // Step 1: Pre-save validation & trigger Confirmation Modal
  const handlePreSaveContact = () => {
    if (
      !formData.name.trim() ||
      !formData.username.trim() ||
      !formData.email.trim() ||
      !formData.role.trim() ||
      !formData.phone.trim() ||
      !formData.department.trim()
    ) {
      showError(
        "Validasi Gagal",
        "Mohon lengkapi nama, username login, email, nomor telepon, departemen, dan jabatan."
      );
      return;
    }

    if (!activeContact && formData.password.trim().length < 6) {
      showError(
        "Password Terlalu Pendek",
        "Harap isi password akses sistem minimal 6 karakter agar pengguna dapat login."
      );
      return;
    }

    if (activeContact && formData.password.trim() !== "" && formData.password.trim().length < 6) {
      showError(
        "Password Terlalu Pendek",
        "Jika ingin mengganti password, masukkan minimal 6 karakter (atau kosongkan untuk mempertahankan password lama)."
      );
      return;
    }

    setIsSaveConfirmOpen(true);
  };

  // Step 2: Execute Save Contact upon user confirmation in Modal
  const handleExecuteSaveContact = async () => {
    const editing = activeContact;
    setIsSaving(true);

    try {
      if (editing) {
        const updated = await masterService.updateContact(editing.id, {
          name: formData.name.trim(),
          username: formData.username.trim(),
          ...(formData.password.trim() ? { password: formData.password.trim() } : {}),
          system_role: formData.system_role,
          email: formData.email.trim(),
          phone: formData.phone.trim(),
          department: formData.department,
          role: formData.role.trim(),
          timezone: formData.timezone,
          working_hours: formData.working_hours,
        });
        queryClient.setQueryData(
          ["contacts"],
          (old: InterviewerContact[] | undefined) => [
            updated,
            ...(old || []).filter((c) => c.id !== editing.id),
          ]
        );
        showSuccess(
          "Berhasil Diperbarui",
          `Data akun & profil "${formData.name}" (@${updated.username || formData.username}) berhasil diperbarui.`
        );
      } else {
        const created = await masterService.createContact({
          employee_id: formData.employee_id.trim(),
          name: formData.name.trim(),
          username: formData.username.trim(),
          password: formData.password.trim(),
          system_role: formData.system_role,
          email: formData.email.trim(),
          phone: formData.phone.trim(),
          department: formData.department,
          role: formData.role.trim(),
          timezone: formData.timezone,
          working_hours: formData.working_hours,
        });
        queryClient.setQueryData(
          ["contacts"],
          (old: InterviewerContact[] | undefined) => [created, ...(old || [])]
        );
        showSuccess(
          "Pengguna & Interviewer Ditambahkan",
          `Akun "${formData.name}" (@${created.username || formData.username}) siap digunakan untuk login dengan role ${formData.system_role}.`
        );
      }
      void queryClient.invalidateQueries({ queryKey: ["contacts"] });
      setIsSaveConfirmOpen(false);
      setIsFormModalOpen(false);
    } catch (error) {
      console.error("Failed to save contact:", error);
      showError(
        "Gagal Menyimpan",
        error instanceof Error
          ? error.message
          : "Terjadi kesalahan sistem saat menyimpan data akun interviewer."
      );
    } finally {
      setIsSaving(false);
    }
  };

  // Confirm Delete (Wired to backend soft-deactivation DELETE /api/v1/contacts/{id})
  const handleConfirmDelete = async () => {
    if (!activeContact) return;
    const deletedId = activeContact.id;
    const deletedName = activeContact.name;
    setIsSaving(true);
    try {
      await masterService.deleteContact(deletedId);
      queryClient.setQueryData(
        ["contacts"],
        (old: InterviewerContact[] | undefined) =>
          (old || []).filter((c) => c.id !== deletedId)
      );
      void queryClient.invalidateQueries({ queryKey: ["contacts"] });
      setIsDeleteModalOpen(false);
      setActiveContact(null);
      showSuccess(
        "Akun Dinonaktifkan",
        `Akses login dan kontak "${deletedName}" telah dinonaktifkan dari sistem.`
      );
    } catch (error) {
      console.error("Failed to deactivate contact:", error);
      showError(
        "Gagal Menonaktifkan Akun",
        error instanceof Error ? error.message : "Terjadi kesalahan saat menonaktifkan pengguna."
      );
    } finally {
      setIsSaving(false);
    }
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
      case "Human Resources":
        return <Badge color="info" size="sm">{dept}</Badge>;
      default:
        return <Badge color="light" size="sm">{dept || "Operations"}</Badge>;
    }
  };

  const renderSystemRoleBadge = (sysRole?: UserRole) => {
    switch (sysRole) {
      case "HR":
        return (
          <span className="inline-flex items-center rounded-md bg-success-50 px-1.5 py-0.5 text-[10px] font-bold text-success-700 dark:bg-success-500/15 dark:text-success-400">
            HR
          </span>
        );
      case "ADMIN":
        return (
          <span className="inline-flex items-center rounded-md bg-brand-50 px-1.5 py-0.5 text-[10px] font-bold text-brand-700 dark:bg-brand-500/15 dark:text-brand-400">
            ADMIN
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center rounded-md bg-blue-light-50 px-1.5 py-0.5 text-[10px] font-bold text-blue-light-700 dark:bg-blue-light-500/15 dark:text-blue-light-400">
            INTERVIEWER
          </span>
        );
    }
  };

  return (
    <div>
      <PageBreadcrumb pageTitle="Interviewer Directory" />

      {/* Main Container */}
      <div className="rounded-2xl border border-gray-200 bg-white p-5 xl:p-6 dark:border-gray-800 dark:bg-gray-900 shadow-theme-xs">
        {/* Header Actions */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between pb-5 border-b border-gray-100 dark:border-gray-800">
          <div>
            <h3 className="text-theme-xl font-semibold text-gray-800 dark:text-white/90">
              Interviewer &amp; Internal System Users
            </h3>
            <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
              Kelola direktori pewawancara, ketersediaan kalender AI Retriever, serta akun login sistem (Role, Username, &amp; Password).
            </p>
          </div>
          <Button
            variant="primary"
            size="sm"
            startIcon={<PlusIcon />}
            onClick={handleOpenAdd}
            disabled={!canManageContacts}
            title={
              !canManageContacts
                ? "Hanya HR atau Admin yang berhak mendaftarkan interviewer baru."
                : undefined
            }
          >
            Add Interviewer
          </Button>
        </div>

        {/* Filter Controls Bar */}
        <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-12">
          <div className="sm:col-span-6">
            <InputField
              placeholder="Search name, username, employee ID, email, or position..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <div className="sm:col-span-3">
            <Select
              options={[
                { value: "ALL", label: "All Department" },
                { value: "Engineering", label: "Engineering" },
                { value: "Product", label: "Product" },
                { value: "Finance", label: "Finance" },
                { value: "People Operations", label: "People Operations" },
                { value: "Human Resources", label: "Human Resources" },
                { value: "Internal Audit", label: "Internal Audit" },
                { value: "Operations", label: "Operations" },
              ]}
              value={selectedDept}
              onChange={(e) => setSelectedDept(e.target.value)}
            />
          </div>

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
                <TableCell
                  isHeader
                  className="ps-4 pe-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300"
                >
                  Interviewer / System Account
                </TableCell>
                <TableCell
                  isHeader
                  className="px-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300"
                >
                  Department &amp; Position
                </TableCell>
                <TableCell
                  isHeader
                  className="px-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300"
                >
                  Timezone
                </TableCell>
                <TableCell
                  isHeader
                  className="px-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300"
                >
                  Working Hours
                </TableCell>
                <TableCell
                  isHeader
                  className="px-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300"
                >
                  Contact
                </TableCell>
                <TableCell
                  isHeader
                  className="pe-5 ps-3 py-3 text-end text-xs font-semibold text-gray-600 dark:text-gray-300"
                >
                  Actions
                </TableCell>
              </TableRow>
            </TableHeader>
            <TableBody className="divide-y divide-gray-100 dark:divide-gray-800">
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={6} className="py-8 text-center text-xs text-gray-400">
                    Loading contacts from database...
                  </TableCell>
                </TableRow>
              ) : filteredContacts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="py-8 text-center text-xs text-gray-400">
                    No contacts match the search filter.
                  </TableCell>
                </TableRow>
              ) : (
                filteredContacts.map((item) => (
                  <TableRow
                    key={item.id}
                    className="hover:bg-gray-50/70 dark:hover:bg-white/[0.02] transition-colors"
                  >
                    {/* Interviewer Info with Avatar & Username/Role */}
                    <TableCell className="ps-4 pe-3 py-3.5">
                      <div className="flex items-center gap-3">
                        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-50 font-semibold text-xs text-brand-600 dark:bg-brand-500/15 dark:text-brand-400 border border-brand-200 dark:border-brand-500/20">
                          {item.avatar_initials}
                        </div>
                        <div className="flex flex-col">
                          <div className="flex flex-wrap items-center gap-1.5">
                            <span className="font-semibold text-sm text-gray-900 dark:text-white/90">
                              {item.name}
                            </span>
                            {renderSystemRoleBadge(item.system_role)}
                          </div>
                          <div className="mt-0.5 flex items-center gap-1.5 text-[11px] font-mono text-gray-400">
                            <span>{item.employee_id}</span>
                            {item.username && (
                              <>
                                <span>&bull;</span>
                                <span className="text-brand-600 dark:text-brand-400">
                                  @{item.username}
                                </span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                    </TableCell>

                    {/* Department & Position */}
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
                        <span className="font-medium text-gray-700 dark:text-gray-300">
                          {item.email}
                        </span>
                        <span className="text-[11px]">{item.phone}</span>
                      </div>
                    </TableCell>

                    {/* Actions */}
                    <TableCell className="pe-5 ps-3 py-3.5 text-end whitespace-nowrap">
                      {canManageContacts ? (
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            type="button"
                            onClick={() => handleOpenEdit(item)}
                            className="h-8 w-8 inline-flex items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-600 shadow-theme-xs hover:border-brand-300 hover:bg-gray-50 hover:text-brand-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:border-brand-500/30 dark:hover:bg-gray-700/60 dark:hover:text-brand-400 transition-all"
                            title="Edit Kontak & Akun Login"
                          >
                            <PencilIcon />
                          </button>
                          <button
                            type="button"
                            onClick={() => {
                              setActiveContact(item);
                              setIsDeleteModalOpen(true);
                            }}
                            className="h-8 w-8 inline-flex items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-500 shadow-theme-xs hover:border-error-300 hover:bg-error-50 hover:text-error-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400 dark:hover:border-error-500/30 dark:hover:bg-error-500/15 dark:hover:text-error-400 transition-all"
                            title="Nonaktifkan Kontak & Akses Login"
                          >
                            <TrashBinIcon />
                          </button>
                        </div>
                      ) : (
                        <span className="text-xs text-gray-400 italic">Read-only</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Footer Summary */}
        <div className="mt-4 flex items-center justify-between text-xs text-gray-400">
          <span>
            Showing {filteredContacts.length} of {contacts.length} active system users
          </span>
          <span className="font-mono">API Contract: tblm_user (Argon2 + RBAC)</span>
        </div>
      </div>

      {/* Unified Interviewer & System Account Form Modal (Add / Edit) */}
      <Modal
        isOpen={isFormModalOpen}
        onClose={() => setIsFormModalOpen(false)}
        className="max-w-4xl m-4"
      >
        <div className="p-8 sm:p-10">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {activeContact ? "Edit Interviewer & System Access" : "Add New Interviewer & System Access"}
          </h3>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            {activeContact
              ? "Perbarui profil departemen, zona waktu, hak akses role sistem, atau reset password login pengguna."
              : "Daftarkan Hiring Manager, Pewawancara, atau Staf HR/Admin baru beserta kredensial login sistem."}
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
                  onChange={(e) =>
                    setFormData({ ...formData, employee_id: e.target.value })
                  }
                />
              </FormField>
            </div>

            {/* System Access Credentials Block */}
            <div className="rounded-xl border border-brand-100 bg-brand-50/40 p-4 dark:border-brand-900/40 dark:bg-brand-950/20">
              <div className="mb-3 flex items-center justify-between">
                <span className="text-xs font-semibold text-gray-800 dark:text-white/90">
                  System Login &amp; Access Control (RBAC)
                </span>
                <span className="text-[10px] font-mono text-brand-600 dark:text-brand-400">
                  Argon2id Encrypted
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <FormField label="System Access Role" required>
                  <Select
                    options={[
                      { value: "INTERVIEWER", label: "Interviewer (Technical / User)" },
                      { value: "HR", label: "HR (Talent Acquisition)" },
                      { value: "ADMIN", label: "Admin (Full System & Audit)" },
                    ]}
                    value={formData.system_role}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        system_role: e.target.value as UserRole,
                      })
                    }
                  />
                </FormField>

                <FormField label="Login Username" required>
                  <InputField
                    placeholder="e.g., budi.santoso"
                    value={formData.username}
                    onChange={(e) =>
                      setFormData({ ...formData, username: e.target.value })
                    }
                  />
                </FormField>

                <FormField
                  label={activeContact ? "New Password (Optional)" : "Login Password"}
                  required={!activeContact}
                >
                  <div className="relative">
                    <InputField
                      type={showPassword ? "text" : "password"}
                      placeholder={
                        activeContact
                          ? "Leave blank to keep current"
                          : "Min. 6 characters"
                      }
                      value={formData.password}
                      onChange={(e) =>
                        setFormData({ ...formData, password: e.target.value })
                      }
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword((prev) => !prev)}
                      className="end-3 absolute top-1/2 z-30 -translate-y-1/2 cursor-pointer text-gray-400 hover:text-gray-600"
                    >
                      {showPassword ? (
                        <EyeIcon className="fill-gray-500 dark:fill-gray-400" />
                      ) : (
                        <EyeCloseIcon className="fill-gray-500 dark:fill-gray-400" />
                      )}
                    </button>
                  </div>
                </FormField>
              </div>
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
                    { value: "Human Resources", label: "Human Resources" },
                    { value: "Internal Audit", label: "Internal Audit" },
                    { value: "Operations", label: "Operations" },
                  ]}
                  value={formData.department}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      department: e.target.value as Department,
                    })
                  }
                />
              </FormField>

              <FormField label="Job Title / Position" required>
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
                  onChange={(e) =>
                    setFormData({ ...formData, timezone: e.target.value as Timezone })
                  }
                />
              </FormField>

              <FormField label="Working Hours" required>
                <InputField
                  placeholder="09:00 - 17:00"
                  value={formData.working_hours}
                  onChange={(e) =>
                    setFormData({ ...formData, working_hours: e.target.value })
                  }
                />
              </FormField>
            </div>
          </div>

          <div className="mt-6 flex justify-end gap-2.5 pt-3 border-t border-gray-100 dark:border-gray-800">
            <Button variant="outline" onClick={() => setIsFormModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handlePreSaveContact}
              disabled={isSaving}
            >
              {activeContact ? "Update Account" : "Save Account"}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Save Confirmation Modal (Add or Edit) */}
      <ConfirmationModal
        isOpen={isSaveConfirmOpen}
        onClose={() => setIsSaveConfirmOpen(false)}
        onConfirm={handleExecuteSaveContact}
        isLoading={isSaving}
        title={activeContact ? "Confirm Update Interviewer" : "Confirm Add Interviewer"}
        description={
          activeContact
            ? "Apakah Anda yakin ingin memperbarui informasi profil dan hak akses login pengguna ini?"
            : `Daftarkan akun "${formData.name}" (@${formData.username}) dengan role sistem ${formData.system_role}?`
        }
        confirmText={activeContact ? "Yes, Save Changes" : "Yes, Register Account"}
        cancelText="Cancel"
        variant="primary"
      />

      {/* Delete Confirmation Modal */}
      <ConfirmationModal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        onConfirm={handleConfirmDelete}
        isLoading={isSaving}
        title="Confirm Deactivate User Account"
        description={`Nonaktifkan kontak & akses login "${activeContact?.name}" (${activeContact?.role})? Riwayat wawancara dan jejak audit historis pengguna ini tetap terjaga.`}
        confirmText="Yes, Deactivate"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
}
