"use client";
import React from "react";

export function ChatMessage({ role, children }: { role: "system" | "user"; children: React.ReactNode }) {
  const isUser = role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`${isUser ? "bg-blue-600 text-white" : "bg-gray-200"} px-3 py-2 rounded-lg max-w-[80%] my-1`}>{children}</div>
    </div>
  );
}

export function ChatInput({ onSend, placeholder, disabled }: { onSend: (text: string)=>void; placeholder?: string; disabled?: boolean }) {
  const [text, setText] = React.useState("");
  return (
    <form onSubmit={(e)=>{e.preventDefault(); if(!text.trim()) return; onSend(text.trim()); setText("");}} className="flex gap-2 pt-2">
      <input className="flex-1 border rounded p-2" placeholder={placeholder ?? "Type..."} value={text} onChange={e=>setText(e.target.value)} disabled={disabled} />
      <button className="bg-black text-white px-3 py-2 rounded disabled:opacity-50" disabled={disabled || !text.trim()}>Send</button>
    </form>
  );
}

