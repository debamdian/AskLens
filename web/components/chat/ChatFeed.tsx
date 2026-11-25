"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Mic, Volume2, VolumeX, Sparkles, AlertCircle } from "lucide-react";
import { MessageItem, MessageData } from "./MessageItem";

export const ChatFeed: React.FC<{ initialPrompt?: string }> = ({ initialPrompt }) => {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<MessageData[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (initialPrompt) {
      handleSend(initialPrompt);
    }
  }, [initialPrompt]);

  const speakText = (text: string) => {
    if (!ttsEnabled || typeof window === "undefined" || !("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const cleanText = text.replace(/[*_#`]/g, "");
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 1.0;
    window.speechSynthesis.speak(utterance);
  };

  const handleSend = async (queryText?: string) => {
    const textToSend = (queryText || input).trim();
    if (!textToSend || isStreaming) return;

    setErrorMsg(null);
    setInput("");

    const userMsgId = `user-${Date.now()}`;
    const assistantMsgId = `asst-${Date.now()}`;

    // 1. Append User Message
    const userMsg: MessageData = {
      id: userMsgId,
      sender: "user",
      content: textToSend,
    };

    // 2. Append Assistant Placeholder
    const assistantMsg: MessageData = {
      id: assistantMsgId,
      sender: "assistant",
      status: "planning",
      statusMessage: "Formulating analysis plan...",
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsStreaming(true);

    try {
      const response = await fetch("http://localhost:8000/api/v1/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: textToSend }),
      });

      if (!response.ok || !response.body) {
        throw new Error(`Server responded with ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const block of lines) {
          if (!block.trim()) continue;

          let eventType = "message";
          let dataStr = "";

          for (const line of block.split("\n")) {
            if (line.startsWith("event:")) {
              eventType = line.replace("event:", "").trim();
            } else if (line.startsWith("data:")) {
              dataStr = line.replace("data:", "").trim();
            }
          }

          if (!dataStr) continue;

          try {
            const parsedData = JSON.parse(dataStr);

            setMessages((prev) =>
              prev.map((msg) => {
                if (msg.id !== assistantMsgId) return msg;

                const updated = { ...msg };

                if (eventType === "status") {
                  updated.status = parsedData.status;
                  updated.statusMessage = parsedData.message;
                } else if (eventType === "plan") {
                  updated.plan = parsedData;
                } else if (eventType === "sql") {
                  updated.sql = parsedData.sql;
                } else if (eventType === "rows") {
                  updated.rowsData = parsedData;
                } else if (eventType === "chart") {
                  updated.chartSpec = parsedData;
                } else if (eventType === "insight") {
                  updated.insight = parsedData.text;
                  speakText(parsedData.text);
                } else if (eventType === "final") {
                  updated.status = "completed";
                  updated.followUps = parsedData.follow_ups;
                } else if (eventType === "error") {
                  updated.status = "completed";
                  updated.insight = `⚠️ Analysis Error: ${parsedData.error}`;
                }

                return updated;
              })
            );
          } catch (e) {
            console.error("Error parsing SSE JSON payload:", e);
          }
        }
      }
    } catch (err: any) {
      setErrorMsg(`Failed to connect to AskLens API: ${err.message}. Is backend running?`);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMsgId
            ? {
                ...msg,
                status: "completed",
                insight: `⚠️ Execution failed: ${err.message}`,
              }
            : msg
        )
      );
    } finally {
      setIsStreaming(false);
    }
  };

  const handleVoiceToggle = () => {
    // MediaRecorder voice flow: triggers in Phase 2 with faster-whisper
    if (!isRecording) {
      setIsRecording(true);
      // Simulated voice prompt demo for Phase 1
      setTimeout(() => {
        setIsRecording(false);
        setInput("Why did sales drop in Gujarat last quarter?");
      }, 1500);
    } else {
      setIsRecording(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-50 dark:bg-slate-950">
      {/* Top Bar */}
      <header className="h-14 border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur px-6 flex items-center justify-between">
        <div className="flex items-center space-x-2 text-xs font-medium text-slate-600 dark:text-slate-300">
          <Sparkles className="w-4 h-4 text-blue-500" />
          <span>AskLens Session Active</span>
          <span className="text-slate-400">|</span>
          <span className="text-emerald-500 font-mono">warehouse.public</span>
        </div>

        <button
          onClick={() => setTtsEnabled(!ttsEnabled)}
          className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs transition-colors border ${
            ttsEnabled
              ? "bg-blue-50 dark:bg-blue-950/60 border-blue-200 dark:border-blue-800 text-blue-600 dark:text-blue-400 font-semibold"
              : "bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-500 hover:text-slate-700"
          }`}
          title="Read answer aloud"
        >
          {ttsEnabled ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
          <span>{ttsEnabled ? "Read Aloud On" : "Read Aloud Off"}</span>
        </button>
      </header>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center max-w-lg mx-auto space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold text-xl shadow-inner">
              ⚡
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100">
                Ask a Question in Plain English or Voice
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                AskLens acts as a Principal Data Analyst: it generates safe SQL, verifies query cost,
                and synthesizes diagnostic answers with charts and tables.
              </p>
            </div>

            <div className="w-full pt-4 space-y-2">
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider text-left">
                Try asking:
              </div>
              {[
                "Why did sales drop in Gujarat last quarter?",
                "What are the top 5 product categories by revenue?",
                "Which customer segments have the highest return rate?",
              ].map((sample, i) => (
                <button
                  key={i}
                  onClick={() => handleSend(sample)}
                  className="w-full text-left p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-blue-400 dark:hover:border-blue-500 hover:shadow-sm transition-all text-xs text-slate-700 dark:text-slate-200 flex items-center justify-between"
                >
                  <span>{sample}</span>
                  <span className="text-blue-500 text-[11px] font-semibold">Run →</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto">
            {messages.map((m) => (
              <MessageItem key={m.id} message={m} onFollowUpClick={(q) => handleSend(q)} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Error notification if any */}
      {errorMsg && (
        <div className="max-w-4xl mx-auto px-6 mb-2 w-full">
          <div className="p-2.5 rounded-lg bg-rose-50 dark:bg-rose-950/60 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        </div>
      )}

      {/* Input Bar */}
      <div className="p-4 bg-white/80 dark:bg-slate-900/80 backdrop-blur border-t border-slate-200 dark:border-slate-800">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="max-w-4xl mx-auto flex items-center space-x-2 bg-slate-100 dark:bg-slate-800 rounded-2xl p-1.5 border border-slate-200 dark:border-slate-700 shadow-sm focus-within:ring-2 focus-within:ring-blue-500/20 focus-within:border-blue-500 transition-all"
        >
          <button
            type="button"
            onClick={handleVoiceToggle}
            className={`p-2.5 rounded-xl transition-colors ${
              isRecording
                ? "bg-rose-500 text-white animate-pulse"
                : "text-slate-500 hover:text-blue-500 hover:bg-slate-200 dark:hover:bg-slate-700"
            }`}
            title="Speak Question (Voice Input)"
          >
            <Mic className="w-4 h-4" />
          </button>

          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              isRecording
                ? "Listening... (Simulating: Why did sales drop in Gujarat?)"
                : "Ask about trends, customer retention, sales drop, or product performance..."
            }
            className="flex-1 bg-transparent px-2 text-sm text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none"
            disabled={isStreaming}
          />

          <button
            type="submit"
            disabled={!input.trim() || isStreaming}
            className="p-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white font-medium transition-all shadow-sm shadow-blue-500/20"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
