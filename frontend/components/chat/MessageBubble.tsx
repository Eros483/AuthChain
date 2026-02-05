type Props = {
  role: "me" | "ai";
  children: React.ReactNode;
};

export default function MessageBubble({ role, children }: Props) {
  if (role === "me") {
    return (
      <div className="self-start">
        <span className="block mb-1 text-[10px] text-neutral-500">
          ME
        </span>
        <div className="rounded-xl bg-pink-100 px-4 py-2 text-sm text-neutral-800">
          {children}
        </div>
      </div>
    );
  }

  return (
    <div className="self-center">
      <span className="block mb-1 text-[10px] text-neutral-500 text-center">
        OUR AI
      </span>
      <div className="rounded-xl bg-gradient-to-r from-pink-200 to-violet-200 px-6 py-3 text-sm">
        {children}
      </div>
    </div>
  );
}
