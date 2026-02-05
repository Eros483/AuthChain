export default function ChatPreview() {
  return (
    <div className="relative rounded-3xl bg-gradient-to-br from-white to-violet-100 p-10 shadow-xl">
      <div className="flex flex-col items-center gap-4 mb-10">
        <div className="text-xl">✦</div>
        <p className="text-sm text-neutral-600">
          Ask our AI anything
        </p>
      </div>

      <div className="flex flex-col gap-3 mb-6">
        <button className="rounded-xl bg-white px-4 py-2 text-left text-sm shadow">
          What can I ask you to do?
        </button>

        <button className="rounded-xl bg-white px-4 py-2 text-left text-sm shadow">
          What projects should I be concerned about right now?
        </button>
      </div>

      <div className="flex items-center gap-3 rounded-xl bg-white px-4 py-3 shadow">
        <input
          className="flex-1 text-sm outline-none placeholder:text-neutral-400"
          placeholder="Ask me anything about your projects"
        />
        <button className="text-lg">➤</button>
      </div>
    </div>
  );
}
