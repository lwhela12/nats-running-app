"use client";
import { useState } from "react";
import Link from "next/link";
import { apiLogin } from "@/lib/api";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const tokens = await apiLogin({ email, password });
      localStorage.setItem("nra_access", tokens.access_token);
      localStorage.setItem("nra_refresh", tokens.refresh_token);
      window.location.href = "/onboarding";
    } catch (err: any) {
      setError(err?.message || "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Welcome back</h1>
      <form onSubmit={onSubmit} className="space-y-4 max-w-sm">
        <input className="w-full border rounded p-2" placeholder="Email" type="email" value={email} onChange={e=>setEmail(e.target.value)} />
        <input className="w-full border rounded p-2" placeholder="Password" type="password" value={password} onChange={e=>setPassword(e.target.value)} />
        {error && <p className="text-red-600 text-sm">{error}</p>}
        <button disabled={loading} className="bg-black text-white px-4 py-2 rounded disabled:opacity-50">{loading?"Logging in...":"Log in"}</button>
      </form>
      <p className="text-sm">No account? <Link className="underline" href="/register">Create one</Link></p>
    </div>
  );
}

