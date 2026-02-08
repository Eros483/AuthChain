"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import ChatInput from "./ChatInput";
import MessageBubble from "./MessageBubble";
import ApprovalCard from "./ApprovalCard";
import SuggestionCards from "./SuggestionCards";
import {
  executeAgent,
  getAgentStatus,
  getAgentResponse,
  getCriticalAction,
  type Message,
  type CriticalAction,
} from "@/lib/api";

interface ChatMessage {
  id: string;
  role: "me" | "ai";
  content: string;
  timestamp: string;
}

export default function ChatCanvas() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [criticalAction, setCriticalAction] = useState<CriticalAction | null>(null);
  const [pollTrigger, setPollTrigger] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const pollerRef = useRef<NodeJS.Timeout | null>(null);
  const [approvalLocked, setApprovalLocked] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (!threadId) return;

    if (pollerRef.current) {
      clearInterval(pollerRef.current);
      pollerRef.current = null;
    }

    pollerRef.current = setInterval(async () => {
      try {
        const status = await getAgentStatus(threadId);

        if (status.status === "AWAITING_APPROVAL") {
          const action = await getCriticalAction(threadId);
          setCriticalAction(action);
          setIsLoading(false);

          clearInterval(pollerRef.current!);
          pollerRef.current = null;
        }

        if (status.status === "COMPLETED") {
          const response = await getAgentResponse(threadId);

          if (response.output?.messages) {
            const aiMessages = response.output.messages.filter(
              (m: Message) => m.type === "ai_message" && m.content
            );

            if (aiMessages.length > 0) {
              const last = aiMessages[aiMessages.length - 1];

              setMessages(prev => [
                ...prev,
                {
                  id: crypto.randomUUID(),
                  role: "ai",
                  content: last.content!,
                  timestamp: last.timestamp,
                },
              ]);

              cleanupPolling();
            }
          }
        }

        if (status.status === "ERROR") {
          setMessages(prev => [
            ...prev,
            {
              id: crypto.randomUUID(),
              role: "ai",
              content: "Execution failed.",
              timestamp: new Date().toISOString(),
            },
          ]);

          cleanupPolling();
        }
      } catch {
        cleanupPolling();
      }
    }, 2000);

    return () => {
      if (pollerRef.current) {
        clearInterval(pollerRef.current);
        pollerRef.current = null;
      }
    };
  }, [threadId, pollTrigger]);

  const cleanupPolling = () => {
    if (pollerRef.current) {
      clearInterval(pollerRef.current);
      pollerRef.current = null;
    }
    setThreadId(null);
    setIsLoading(false);
    setCriticalAction(null);
  };

  const handleSendMessage = async (query: string) => {
    setCriticalAction(null);
    setThreadId(null);

    setMessages(prev => [
      ...prev,
      {
        id: crypto.randomUUID(),
        role: "me",
        content: query,
        timestamp: new Date().toISOString(),
      },
    ]);

    setIsLoading(true);

    try {
      const result = await executeAgent(query);
      setThreadId(result.thread_id);
      setPollTrigger(p => p + 1);
    } catch {
      setMessages(prev => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "ai",
          content: "Failed to start agent.",
          timestamp: new Date().toISOString(),
        },
      ]);
      setIsLoading(false);
    }
  };

  const handleApprovalResponse = (approved: boolean, currentThreadId: string) => {
    setApprovalLocked(true);
    setCriticalAction(null);
    setIsLoading(true);

    if (approved) {
      setMessages(prev => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "ai",
          content:
            "Approved by AI governance. Awaiting on-chain execution approval…",
          timestamp: new Date().toISOString(),
        },
      ]);

      setPollTrigger(p => p + 1);
    } else {
      setMessages(prev => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "ai",
          content: "Action rejected. Execution halted.",
          timestamp: new Date().toISOString(),
        },
      ]);

      cleanupPolling();
    }
  };

  const showWelcome = messages.length === 0 && !isLoading;

  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-[#0B0E14]">
      <div className="absolute top-6 left-6 z-20">
        <Link
          href="/"
          className="flex items-center gap-2 text-sm text-[#9BA3B4] hover:text-[#E6E8EB]"
        >
          ← Back to Home
        </Link>
      </div>

      <div className="relative flex flex-col min-h-screen">
        {showWelcome && (
          <div className="flex-1 flex flex-col items-center justify-center text-center">
            <h1 className="text-5xl font-bold text-white">AuthChain</h1>
            <p className="text-[#9BA3B4] mt-3">
              Agent Execution enforced by on-chain governance
            </p>
          </div>
        )}

        {!showWelcome && (
          <div className="flex-1 overflow-y-auto px-8">
            <div className="max-w-4xl mx-auto py-8 space-y-6">
              {messages.map(msg => (
                <MessageBubble key={msg.id} role={msg.role}>
                  {msg.content}
                </MessageBubble>
              ))}

              {isLoading && !criticalAction && (
                <MessageBubble role="ai">Processing...</MessageBubble>
              )}

              {criticalAction && (
                <ApprovalCard
                  action={criticalAction}
                  threadId={criticalAction.thread_id}
                  onResponse={handleApprovalResponse}
                />
              )}

              <div ref={messagesEndRef} />
            </div>
          </div>
        )}

        <div className="px-8 pb-8">
          <div className="max-w-4xl mx-auto">
            {showWelcome && <SuggestionCards onSelect={handleSendMessage} />}
            <ChatInput onSend={handleSendMessage} disabled={isLoading} />
          </div>
        </div>
      </div>
    </div>
  );
}
