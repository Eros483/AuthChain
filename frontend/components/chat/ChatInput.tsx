export default function ChatInput() {
  return (
    <div className="mt-10">
      <div className="flex items-center gap-4 rounded-xl border border-neutral-300 bg-white px-4 py-3">
        <input
          className="flex-1 text-sm outline-none placeholder:text-neutral-400"
          placeholder="Ask me anything about your projects"
        />
        <button className="text-2xl text-neutral-500">
          ➤
        </button>
      </div>
    </div>
  );
}
