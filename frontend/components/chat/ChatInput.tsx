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
      <div className="flex items-center gap-4 rounded-xl border border-neutral-300 bg-white/80 backdrop-blur-sm px-5 py-3 shadow-sm">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={disabled}
          className="flex-1 text-sm outline-none placeholder:text-neutral-400 bg-transparent disabled:opacity-50"
          placeholder="Ask me anything about your projects"
        />
        <button
          type="submit"
          disabled={disabled || !input.trim()}
          className="text-2xl text-neutral-500 hover:text-neutral-700 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
        >
          ➤
        </button>
      </div>
    </form>
  );
}
