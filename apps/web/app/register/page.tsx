"use client";
import { useState } from "react";
import Link from "next/link";
import { apiRegister } from "@/lib/api";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [age, setAge] = useState<number>(30);
  const [sex, setSex] = useState("other");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const tokens = await apiRegister({ email, password, age, sex });
      localStorage.setItem("nra_access", tokens.access_token);
      localStorage.setItem("nra_refresh", tokens.refresh_token);
      window.location.href = "/onboarding";
    } catch (err: any) {
      setError(err?.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Create your account</h1>
      <form onSubmit={onSubmit} className="space-y-4 max-w-sm">
        <input className="w-full border rounded p-2" placeholder="Email" type="email" value={email} onChange={e=>setEmail(e.target.value)} />
        <input className="w-full border rounded p-2" placeholder="Password (min 8)" type="password" value={password} onChange={e=>setPassword(e.target.value)} />
        <input className="w-full border rounded p-2" placeholder="Age" type="number" value={age} onChange={e=>setAge(Number(e.target.value))} />
        <select className="w-full border rounded p-2" value={sex} onChange={e=>setSex(e.target.value)}>
          <option value="male">Male</option>
          <option value="female">Female</option>
          <option value="other">Other</option>
        </select>
        {error && <p className="text-red-600 text-sm">{error}</p>}
        <button disabled={loading} className="bg-black text-white px-4 py-2 rounded disabled:opacity-50">{loading?"Creating...":"Create account"}</button>
      </form>
      <p className="text-sm">Have an account? <Link className="underline" href="/login">Log in</Link></p>
    </div>
  );
}

