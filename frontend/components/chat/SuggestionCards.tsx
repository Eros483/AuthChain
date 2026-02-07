"use client";

interface Props {
  onSelect: (suggestion: string) => void;
}

const suggestions = [
  "Build a simple MLP wrapper class.",
  "Commit all pending changes.",
  "Delete the database.",
];

export default function SuggestionCards({ onSelect }: Props) {
  return (
    <div className="mb-6">
      <p className="text-center text-sm text-[#9BA3B4] mb-4">
        Suggestions to see how AuthChain helps you handle critical actions
      </p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {suggestions.map((suggestion, index) => (
          <button
            key={index}
            onClick={() => onSelect(suggestion)}
            className="text-left text-sm text-[#E6E8EB] bg-[#121826] px-4 py-3 rounded-lg border border-[#1E2638] hover:bg-[#1A2332] hover:border-[#4DA3FF]/50 transition-all"
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
}