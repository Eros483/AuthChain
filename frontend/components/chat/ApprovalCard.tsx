"use client";

import { useState } from "react";
import { submitApproval, type CriticalAction } from "@/lib/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Props {
  action: CriticalAction;
  threadId: string;
  onResponse: (approved: boolean, threadId: string) => void;
}

export default function ApprovalCard({ action, threadId, onResponse }: Props) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [showRejectInput, setShowRejectInput] = useState(false);
  const [rejectReason, setRejectReason] = useState("");

  const handleAuthorize = async () => {
    if (isProcessing) return; 
    
    setIsProcessing(true);
    try {
      await submitApproval(threadId, true);
      onResponse(true, threadId);
    } catch (err) {
      console.error("Authorization failed:", err);
      setIsProcessing(false);
    }
  };

  const handleDeny = async () => {
    if (!rejectReason.trim()) {
      setShowRejectInput(true);
      return;
    }

    if (isProcessing) return; 

    setIsProcessing(true);
    try {
      await submitApproval(threadId, false, rejectReason);
      onResponse(false, threadId);
    } catch (err) {
      console.error("Denial failed:", err);
      setIsProcessing(false);
    }
  };

  return (
    <div className="border border-[#1E2638] bg-[#121826] rounded-lg p-6 shadow-[0_20px_40px_rgba(0,0,0,0.6)]">
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-[#E6E8EB]">
          Authorization Required
        </h3>
        <p className="text-xs text-[#9BA3B4] mt-1">
          This operation exceeds autonomous execution limits and requires explicit approval.
        </p>
      </div>

      <div className="space-y-3 text-sm text-[#E6E8EB]">
        <div>
          <span className="font-medium text-[#E6E8EB]">Operation</span>
          <div className="mt-1 font-mono text-xs bg-[#1A2332] text-[#4DA3FF] px-2 py-1 rounded">
            {action.tool_name}
          </div>
        </div>

        <div>
          <div className="text-[#9BA3B4] mt-1 prose prose-invert prose-sm max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {action.reasoning_summary}
            </ReactMarkdown>
          </div>
        </div>

        <div>
          <span className="font-medium text-[#E6E8EB]">Impact</span>
          <p className="text-[#9BA3B4] mt-1">
            Modifies project state and may affect downstream execution.
          </p>
        </div>

        <details className="mt-2">
          <summary className="cursor-pointer text-xs text-[#9BA3B4] hover:text-[#E6E8EB]">
            View raw execution payload
          </summary>
          <pre className="mt-2 bg-[#1A2332] p-3 rounded text-xs overflow-x-auto whitespace-pre-wrap break-words text-[#9BA3B4]">
            {JSON.stringify(action.tool_arguments, null, 2)}
          </pre>
        </details>
      </div>

      {showRejectInput && !isProcessing && (
        <div className="mt-4">
          <label className="block text-xs font-medium text-[#E6E8EB] mb-1">
            Reason for denial
          </label>
          <textarea
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            rows={3}
            className="w-full border border-[#1E2638] bg-[#1A2332] rounded-md px-3 py-2 text-sm text-[#E6E8EB] placeholder-[#9BA3B4] focus:outline-none focus:ring-1 focus:ring-[#4DA3FF] focus:border-[#4DA3FF]"
            placeholder="Explain why this action should not be executed"
          />
        </div>
      )}

      <div className="mt-6 flex gap-3">
        <button
          onClick={handleAuthorize}
          disabled={isProcessing}
          className="flex-1 bg-[#4DA3FF] text-[#0B0E14] px-4 py-2 rounded-md text-sm font-medium hover:bg-[#6CB6FF] disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          {isProcessing ? "Authorizing..." : "Authorize Execution"}
        </button>

        <button
          onClick={handleDeny}
          disabled={isProcessing}
          className="flex-1 bg-[#1A2332] border border-[#1E2638] px-4 py-2 rounded-md text-sm font-medium text-[#E6E8EB] hover:bg-[#1E2638] disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          {isProcessing ? "Processing..." : "Deny Action"}
        </button>
      </div>
    </div>
  );
}