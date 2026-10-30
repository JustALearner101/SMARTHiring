import type { Metadata } from "next";
import { DashboardContent } from "@/components/dashboard/DashboardContent";

export const metadata: Metadata = {
  title: "Dashboard | SmartHiring AI Orchestrator",
  description: "Executive and operational dashboard for SmartHiring AI Orchestrator",
};

export default function DashboardPage() {
  return <DashboardContent />;
}
