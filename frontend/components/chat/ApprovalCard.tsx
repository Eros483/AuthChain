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

    await submitApproval(threadId, true);
    onResponse(true, threadId);
  };

  const handleDeny = async () => {
    if (!rejectReason.trim()) {
      setShowRejectInput(true);
      return;
    }

    if (isProcessing) return;
    setIsProcessing(true);

    await submitApproval(threadId, false, rejectReason);
    onResponse(false, threadId);
  };

  return (
    <div className="border border-[#1E2638] bg-[#121826] rounded-lg p-6">
      <h3 className="text-sm font-semibold text-white mb-1">
        Governance Approval Required
      </h3>

      <p className="text-xs text-[#9BA3B4] mb-4">
        AI approval does not execute the action. Final execution requires on-chain approval.
      </p>

      <div className="text-sm text-white space-y-3">
        <div className="font-mono text-xs bg-[#1A2332] text-[#4DA3FF] px-2 py-1 rounded">
          {action.tool_name}
        </div>

        <div className="prose prose-invert prose-sm">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {action.reasoning_summary}
          </ReactMarkdown>
        </div>
      </div>

      {showRejectInput && (
        <textarea
          value={rejectReason}
          onChange={e => setRejectReason(e.target.value)}
          rows={3}
          className="w-full mt-4 bg-[#1A2332] border border-[#1E2638] rounded px-3 py-2 text-sm text-white"
          placeholder="Reason for denial"
        />
      )}

      <div className="mt-6 flex gap-3">
        <button
          onClick={handleAuthorize}
          disabled={isProcessing}
          className="flex-1 bg-[#4DA3FF] text-black px-4 py-2 rounded"
        >
          Approve AI Decision
        </button>

        <button
          onClick={handleDeny}
          disabled={isProcessing}
          className="flex-1 bg-[#1A2332] border border-[#1E2638] px-4 py-2 rounded text-white"
        >
          Deny
        </button>
      </div>
    </div>
  );
}
