"use client";

interface Props {
  onSelect: (suggestion: string) => void;
}

const suggestions = [
  "What can I ask you to do?",
  "Which one of my projects is performing the best?",
  "What projects should I be concerned about right now?",
];

export default function SuggestionCards({ onSelect }: Props) {
  return (
    <div className="mb-6">
      <p className="text-xs text-neutral-500 mb-3">
        Suggestions on what to ask Our AI
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
