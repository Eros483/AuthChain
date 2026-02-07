"use client";

import { useState } from "react";
import { submitApproval, type CriticalAction } from "@/lib/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Props {
  action: CriticalAction;
  threadId: string;
  onResponse: (approved: boolean) => void;
}

export default function ApprovalCard({ action, threadId, onResponse }: Props) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [showRejectInput, setShowRejectInput] = useState(false);
  const [rejectReason, setRejectReason] = useState("");

  const handleAuthorize = async () => {
    setIsProcessing(true);
    try {
      await submitApproval(threadId, true);
      onResponse(true);
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

    setIsProcessing(true);
    try {
      await submitApproval(threadId, false, rejectReason);
      onResponse(false);
    } catch (err) {
      console.error("Denial failed:", err);
      setIsProcessing(false);
    }
  };

  return (
    <div className="border border-neutral-300 bg-white rounded-lg p-6 shadow-sm">
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-neutral-900">
          Authorization Required
        </h3>
        <p className="text-xs text-neutral-500 mt-1">
          This operation exceeds autonomous execution limits and requires explicit approval.
        </p>
      </div>

      <div className="space-y-3 text-sm text-neutral-800">
        <div>
          <span className="font-medium">Operation</span>
          <div className="mt-1 font-mono text-xs bg-neutral-100 px-2 py-1 rounded">
            {action.tool_name}
          </div>
        </div>

        <div>
          <p className="text-neutral-600 mt-1">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {action.reasoning_summary}
              </ReactMarkdown>          
          </p>
        </div>

        <div>
          <span className="font-medium">Impact</span>
          <p className="text-neutral-600 mt-1">
            Modifies project state and may affect downstream execution.
          </p>
        </div>

        <details className="mt-2">
          <summary className="cursor-pointer text-xs text-neutral-500">
            View raw execution payload
          </summary>
        <pre className="mt-2 bg-neutral-100 p-3 rounded text-xs overflow-x-auto whitespace-pre-wrap break-words">
          {JSON.stringify(action.tool_arguments, null, 2)}
        </pre>
        </details>
      </div>

      {showRejectInput && !isProcessing && (
        <div className="mt-4">
          <label className="block text-xs font-medium text-neutral-700 mb-1">
            Reason for denial
          </label>
          <textarea
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            rows={3}
            className="w-full border border-neutral-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-neutral-400"
            placeholder="Explain why this action should not be executed"
          />
        </div>
      )}

      <div className="mt-6 flex gap-3">
        <button
          onClick={handleAuthorize}
          disabled={isProcessing}
          className="flex-1 bg-neutral-900 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-neutral-800 disabled:opacity-50"
        >
          {isProcessing ? "Authorizing..." : "Authorize Execution"}
        </button>

        <button
          onClick={handleDeny}
          disabled={isProcessing}
          className="flex-1 bg-white border border-neutral-300 px-4 py-2 rounded-md text-sm font-medium text-neutral-700 hover:bg-neutral-100 disabled:opacity-50"
        >
          {isProcessing ? "Processing..." : "Deny Action"}
        </button>
      </div>
    </div>
  );
}
