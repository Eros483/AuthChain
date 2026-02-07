import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type Props = {
  role: "me" | "ai";
  children: React.ReactNode;
};

export default function MessageBubble({ role, children }: Props) {
  return (
    <div className={`flex ${role === "me" ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-3 ${
          role === "me"
            ? "bg-[#4DA3FF] text-[#0B0E14]"
            : "border border-[#1E2638] bg-[#121826] text-[#E6E8EB]"
        }`}
      >
        {role === "ai" && typeof children === "string" ? (
          <div className="prose prose-invert prose-sm max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {children}
            </ReactMarkdown>
          </div>
        ) : (
          children
        )}
      </div>
    </div>
  );
}