"use client";

import { useState } from "react";
import Link from "next/link";

export default function LoginGate({ onSuccess }: { onSuccess: () => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const submit = () => {
    if (username === "root" && password === "hacktu_7.0") {
      onSuccess();
    } else {
      setError("Invalid credentials");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0B0E14]">
      <div className="w-full max-w-sm bg-[#121826] p-6 rounded-lg border border-white/10">
        <h2 className="text-xl mb-4 text-white">Admin Login</h2>
              <div className="absolute top-6 left-6 z-20">
                <Link
                  href="/"
                  className="flex items-center gap-2 text-sm text-[#9BA3B4] hover:text-[#E6E8EB] transition-colors group"
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
                  <span>Back to Home</span>
                </Link>
              </div>
        <input
          className="w-full mb-3 px-3 py-2 bg-black/40 border border-white/10 rounded"
          placeholder="username"
          value={username}
          onChange={e => setUsername(e.target.value)}
        />

        <input
          type="password"
          className="w-full mb-3 px-3 py-2 bg-black/40 border border-white/10 rounded"
          placeholder="password"
          value={password}
          onChange={e => setPassword(e.target.value)}
        />

        {error && <p className="text-red-400 text-sm mb-2">{error}</p>}

        <button
          onClick={submit}
          className="w-full bg-[#4DA3FF] text-black py-2 rounded font-medium"
        >
          Login
        </button>
      </div>
    </div>
  );
}
