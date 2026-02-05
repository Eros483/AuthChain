import Link from "next/link";
import ChatInput from "./ChatInput";
import MessageBubble from "./MessageBubble";

export default function ChatCanvas() {
  return (
    <div className="relative min-h-screen w-full overflow-hidden">
      
      <div className="absolute inset-0 bg-gradient-to-br from-pink-200/40 via-transparent to-violet-300/40 pointer-events-none" />

      <div className="relative flex flex-col min-h-screen">

        <div className="relative pt-16 pb-10 flex flex-col items-center gap-4">

          <Link
            href="/"
            className="absolute left-10 top-16 text-sm text-neutral-600 hover:text-neutral-900 transition"
          >
            ← Back
          </Link>

          <div className="text-xl text-[#1b0b1f]">✦</div>
          <p className="text-base text-[#1b0b1f]">
            Ask our AI anything
          </p>
        </div>

        <div className="flex-1 px-16 flex flex-col justify-end gap-6">
          <MessageBubble role="ai">✦</MessageBubble>
        </div>

        <div className="px-16 pb-10 pt-6">
          <ChatInput />
        </div>
      </div>
    </div>
  );
}
