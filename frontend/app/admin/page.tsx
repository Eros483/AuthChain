"use client";

import { useState } from "react";
import LoginGate from "@/components/admin/LoginGate";
import ValidatorForm from "@/components/admin/ValidatorForm";
import ValidatorList from "@/components/admin/ValidatorList";
import Link from "next/link";

export default function AdminPage() {
  const [authenticated, setAuthenticated] = useState(false);

  if (!authenticated) {
    return <LoginGate onSuccess={() => setAuthenticated(true)} />;
  }

  return (
    <main className="min-h-screen bg-[#0B0E14] text-[#E6E8EB] px-10 py-8">
      <div className="mb-6">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm text-[#9BA3B4] hover:text-[#E6E8EB] transition-colors group"
        >
          <svg
            className="w-5 h-5 transition-transform group-hover:-translate-x-1"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10 19l-7-7m0 0l7-7m-7 7h18"
            />
          </svg>
          Back to Home
        </Link>
      </div>

      <h1 className="text-3xl font-semibold mb-6">
        Admin · Validator Control
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
        <ValidatorForm />
        <ValidatorList />
      </div>
    </main>
  );
}
