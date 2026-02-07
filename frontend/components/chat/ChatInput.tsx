"use client";

import { useState } from "react";

interface Props {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export default function ChatInput({ onSend, disabled }: Props) {
  const [input, setInput] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput("");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="mt-6">
      <div className="flex items-center gap-4 rounded-xl border border-[#1E2638] bg-[#121826] px-5 py-3 shadow-sm">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={disabled}
          className="flex-1 text-sm outline-none placeholder:text-[#9BA3B4] bg-transparent text-[#E6E8EB] disabled:opacity-50"
          placeholder="Ask me anything about your projects"
        />
        <button
          type="submit"
          disabled={disabled || !input.trim()}
          className="text-2xl text-[#4DA3FF] hover:text-[#6CB6FF] transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
        >
          ➤
        </button>
      </div>
    </form>
  );
}