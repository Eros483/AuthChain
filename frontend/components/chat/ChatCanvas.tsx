"use client";

import { useState, useEffect, useRef } from "react";
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
  const [executionStage, setExecutionStage] = useState<
    "ANALYZING" | "PLANNING" | "DETECTED_CRITICAL" | "AWAITING_APPROVAL" | "EXECUTING" | null
  >(null);


  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (!threadId) return;

    const pollStatus = async () => {
      try {
        const status = await getAgentStatus(threadId);

        if (status.status === "AWAITING_APPROVAL") {
          const action = await getCriticalAction(threadId);
          setCriticalAction(action);
          setIsLoading(false);
        } else if (status.status === "COMPLETED") {
          const response = await getAgentResponse(threadId);

          if (response.output?.messages) {
            const aiMessages = response.output.messages.filter(
              (m: Message) => m.type === "ai_message" && m.content
            );

            if (aiMessages.length > 0) {
              const lastMessage = aiMessages[aiMessages.length - 1];
              setMessages((prev) => [
                ...prev,
                {
                  id: Date.now().toString(),
                  role: "ai",
                  content: lastMessage.content || response.output?.summary || "Task completed",
                  timestamp: lastMessage.timestamp,
                },
              ]);
            }
          }

          setIsLoading(false);
          setThreadId(null);
        } else if (status.status === "ERROR") {
          setMessages((prev) => [
            ...prev,
            {
              id: Date.now().toString(),
              role: "ai",
              content: "An error occurred during execution.",
              timestamp: new Date().toISOString(),
            },
          ]);
          setIsLoading(false);
          setThreadId(null);
        }
      } catch (error) {
        console.error("Polling error:", error);
      }
    };

    const interval = setInterval(pollStatus, 2000);
    return () => clearInterval(interval);
  }, [threadId]);

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
    setCriticalAction(null);

    if (approved) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: "ai",
          content: "Action approved. Continuing execution...",
          timestamp: new Date().toISOString(),
        },
      ]);
    } else {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: "ai",
          content: "Action rejected. Task cancelled.",
          timestamp: new Date().toISOString(),
        },
      ]);
      setIsLoading(false);
      setThreadId(null);
    }
  };

  const showWelcome = messages.length === 0 && !isLoading;

  return (
    <div className="relative min-h-screen w-full overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-pink-200/40 via-transparent to-violet-300/40 pointer-events-none" />

      <div className="relative flex flex-col min-h-screen">

        {showWelcome && (
          <div className="flex-1 flex flex-col items-center justify-center gap-6 px-8 text-center">
           
            <div className="flex flex-col items-center">
              {/* AuthChain - Bold and cleaner, sized correctly */}
              <h1 className="text-5xl font-bold text-[#1b0b1f] tracking-tight">
                AuthChain
              </h1>

              {/* Tagline - Smaller and italicized */}
              <p className="text-sm md:text-base text-[#1b0b1f]/90 italic font-medium leading-relaxed max-w-lg">
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
                  <div className="flex items-center gap-2">
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
