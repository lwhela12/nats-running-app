"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function HomePage() {
  const router = useRouter();
  useEffect(() => {
    const access = localStorage.getItem("nra_access");
    router.replace(access ? "/onboarding" : "/login");
  }, [router]);
  return null;
}

