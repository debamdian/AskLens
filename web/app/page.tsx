"use client";

import React, { useState } from "react";
import { Sidebar } from "@/components/sidebar/Sidebar";
import { ChatFeed } from "@/components/chat/ChatFeed";

export default function Home() {
  const [sessionKey, setSessionKey] = useState(1);
  const [initialPrompt, setInitialPrompt] = useState<string | undefined>(undefined);

  const handleNewChat = () => {
    setInitialPrompt(undefined);
    setSessionKey((prev) => prev + 1);
  };

  const handleSelectSample = (query: string) => {
    setInitialPrompt(query);
    setSessionKey((prev) => prev + 1);
  };

  return (
    <main className="flex h-screen w-screen overflow-hidden">
      <Sidebar onNewChat={handleNewChat} onSelectSampleQuery={handleSelectSample} />
      <ChatFeed key={sessionKey} initialPrompt={initialPrompt} />
    </main>
  );
}
