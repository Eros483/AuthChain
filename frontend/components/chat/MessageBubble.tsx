type Props = {
  role: "me" | "ai";
  children: React.ReactNode;
};

export default function MessageBubble({ role, children }: Props) {
  if (role === "me") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%]">
          <span className="block mb-1 text-[10px] text-neutral-500 uppercase text-right">
            Me
          </span>
          <div className="rounded-xl bg-pink-100/80 backdrop-blur-sm px-5 py-3 text-sm text-neutral-800 shadow-sm">
            {children}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
      <div className="max-w-[80%]">
        <span className="block mb-1 text-[10px] text-neutral-500 uppercase">
          Our AI
        </span>
        <div className="rounded-xl bg-gradient-to-r from-pink-200/80 to-violet-200/80 backdrop-blur-sm px-5 py-3 text-sm text-neutral-800 shadow-sm">
          {children}
        </div>
      </div>
    </div>
  );
}
