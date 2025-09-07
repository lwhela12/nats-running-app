import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Nat's Running App",
  description: "MVP running coach",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <div className="max-w-3xl mx-auto p-4">{children}</div>
      </body>
    </html>
  );
}

