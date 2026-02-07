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
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const pollerRef = useRef<NodeJS.Timeout | null>(null);
  
  type ExecutionStage =
    | "ANALYZING"
    | "PLANNING"
    | "DETECTED_CRITICAL"
    | "AWAITING_APPROVAL"
    | "EXECUTING"
    | null;
  
  const [executionStage, setExecutionStage] = useState<ExecutionStage>(null);


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
        
          const aiMessages =
            response.output?.messages?.filter(
              (m: Message) => m.type === "ai_message" && m.content
            ) ?? [];
          
          if (aiMessages.length) {
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
          }
        
          cleanupPolling();
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
      } catch (e) {
        console.error(e);
        cleanupPolling();
      }
    }, 3000);
  
    return cleanupPolling;
  }, [threadId]);
  
  const cleanupPolling = () => {
    if (pollerRef.current) {
      clearInterval(pollerRef.current);
      pollerRef.current = null;
    }
    setThreadId(null);
    setIsLoading(false);
  };

  const handleSendMessage = async (query: string) => {
    setCriticalAction(null);
    setThreadId(null);

    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        role: "me",
        content: query,
        timestamp: new Date().toISOString(),
      },
    ]);

    setIsLoading(true);

    try {
      const result = await executeAgent(query);
      setThreadId(result.thread_id);
    } catch (error) {
      console.error("Error executing agent:", error);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: "ai",
          content: "Failed to start agent. Please try again.",
          timestamp: new Date().toISOString(),
        },
      ]);
      setIsLoading(false);
    }
  };

  const handleApprovalResponse = (approved: boolean) => {
    cleanupPolling();
    setCriticalAction(null);

    if (approved) {
      setMessages(prev => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "ai",
          content: "Approved. Executing authorized action…",
          timestamp: new Date().toISOString(),
        },
      ]);
    } else {
      setMessages(prev => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "ai",
          content: "Action rejected. Execution stopped.",
          timestamp: new Date().toISOString(),
        },
      ]);
    }
  };

  const showWelcome = messages.length === 0 && !isLoading;

  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-[#0B0E14]">
      {/* Matching gradient from home page */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-1/3 h-[700px] w-[700px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[radial-gradient(circle,rgba(77,163,255,0.12)_0%,rgba(11,14,20,0.95)_60%)]" />
      </div>

      {/* Back Button */}
      <div className="absolute top-6 left-6 z-20">
        <Link
          href="/"
          className="flex items-center gap-2 text-sm text-[#9BA3B4] hover:text-[#E6E8EB] transition-colors group"
        >
          <svg
            className="w-5 h-5 transition-transform group-hover:-translate-x-1"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10 19l-7-7m0 0l7-7m-7 7h18"
            />
          </svg>
          <span>Back to Home</span>
        </Link>
      </div>

      <div className="relative flex flex-col min-h-screen">
        {showWelcome && (
          <div className="flex-1 flex flex-col items-center justify-center gap-6 px-8 text-center">
            <div className="flex flex-col items-center">
              <h1 className="text-5xl font-bold text-[#E6E8EB] tracking-tight">
                AuthChain
              </h1>
              <p className="text-sm md:text-base text-[#9BA3B4] italic font-medium leading-relaxed max-w-lg mt-3">
                Agent Execution powered with Blockchain governance
              </p>
            </div>
          </div>
        )}

        {!showWelcome && (
          <div className="flex-1 px-8 md:px-16 overflow-y-auto">
            <div className="max-w-4xl mx-auto py-8 space-y-6">
              {messages.map((msg) => (
                <MessageBubble key={msg.id} role={msg.role}>
                  {msg.content}
                </MessageBubble>
              ))}

              {isLoading && !criticalAction && (
                <MessageBubble role="ai">
                  <div className="flex items-center gap-2 text-[#9BA3B4]">
                    <div className="animate-pulse">Processing...</div>
                  </div>
                </MessageBubble>
              )}

              {criticalAction && threadId && (
                <ApprovalCard
                  key={threadId}
                  action={criticalAction}
                  threadId={threadId}
                  onResponse={handleApprovalResponse}
                />
              )}

              <div ref={messagesEndRef} />
            </div>
          </div>
        )}

        <div className="px-8 md:px-16 pb-8">
          <div className="max-w-4xl mx-auto">
            {showWelcome && <SuggestionCards onSelect={handleSendMessage} />}
            <ChatInput onSend={handleSendMessage} disabled={isLoading} />
          </div>
        </div>
      </div>
    </div>
  );
}