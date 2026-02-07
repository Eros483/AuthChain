"use client";

import { useState } from "react";
import { submitApproval, type CriticalAction } from "@/lib/api";

interface Props {
  action: CriticalAction;
  threadId: string;
  onResponse: (approved: boolean) => void;
}

export default function ApprovalCard({ action, threadId, onResponse }: Props) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [showRejectInput, setShowRejectInput] = useState(false);
  const [rejectReason, setRejectReason] = useState("");

  const handleApprove = async () => {
    setIsProcessing(true);
    try {
      await submitApproval(threadId, true);
      onResponse(true);
    } catch (error) {
      console.error("Approval error:", error);
      setIsProcessing(false);
    }
  };

  const handleReject = async () => {
    if (!rejectReason.trim()) {
      setShowRejectInput(true);
      return;
    }

    setIsProcessing(true);
    try {
      await submitApproval(threadId, false, rejectReason);
      onResponse(false);
    } catch (error) {
      console.error("Rejection error:", error);
      setIsProcessing(false);
    }
  };

  return (
    <div className="bg-gradient-to-r from-orange-50 to-red-50 border border-orange-200 rounded-xl p-6 shadow-sm">
      <div className="flex items-start gap-3 mb-4">
        <div className="text-2xl">⚠️</div>
        <div className="flex-1">
          <h3 className="font-semibold text-neutral-800 mb-2">
            Critical Action Requires Approval
          </h3>
          <div className="space-y-2 text-sm">
            <div>
              <span className="font-medium text-neutral-700">Tool:</span>{" "}
              <code className="bg-white/60 px-2 py-0.5 rounded text-xs">
                {action.tool_name}
              </code>
            </div>
            <div>
              <span className="font-medium text-neutral-700">Arguments:</span>
              <pre className="bg-white/60 px-3 py-2 rounded text-xs mt-1 overflow-x-auto">
                {JSON.stringify(action.tool_arguments, null, 2)}
              </pre>
            </div>
            <div>
              <span className="font-medium text-neutral-700">Reason:</span>
              <p className="text-neutral-600 mt-1">{action.reasoning_summary}</p>
            </div>
          </div>
        </div>
      </div>

      {showRejectInput && !isProcessing && (
        <div className="mb-4">
          <label className="block text-sm font-medium text-neutral-700 mb-2">
            Please provide a reason for rejection:
          </label>
          <textarea
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-orange-300"
            rows={3}
            placeholder="Why are you rejecting this action?"
          />
        </div>
      )}

      <div className="flex gap-3">
        <button
          onClick={handleApprove}
          disabled={isProcessing}
          className="flex-1 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isProcessing ? "Processing..." : "Approve"}
        </button>
        <button
          onClick={handleReject}
          disabled={isProcessing}
          className="flex-1 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-medium text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isProcessing ? "Processing..." : "Reject"}
        </button>
      </div>
    </div>
  );
}
