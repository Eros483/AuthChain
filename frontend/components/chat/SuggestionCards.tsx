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
      <p className="text-xs text-neutral-500 mb-3">
        Suggestions to see how AuthChain helps you handle critical actions
      </p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {suggestions.map((suggestion, index) => (
          <button
            key={index}
            onClick={() => onSelect(suggestion)}
            className="text-left text-sm text-neutral-600 bg-white/60 backdrop-blur-sm px-4 py-3 rounded-lg border border-neutral-200 hover:bg-white/80 hover:border-neutral-300 transition-all"
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
}
