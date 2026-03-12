import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Toaster } from "sonner";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ZKValue - ZK Proof Layer for Opaque Assets",
  description:
    "Verifiable computation for alternative asset valuation. Trustless, continuous, auditable.",
  keywords: [
    "ZK proofs",
    "private credit",
    "AI valuation",
    "asset verification",
    "cryptographic proof",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // Inline script prevents flash of wrong theme (FOUC)
  const themeScript = `(function(){try{var t=localStorage.getItem('zkvalue-theme');if(t==='dark'||(!t&&window.matchMedia('(prefers-color-scheme:dark)').matches)){document.documentElement.classList.add('dark')}}catch(e){}})()`;

  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} font-sans antialiased`}
      >
        {children}
        <Toaster position="top-right" richColors duration={4000} />
      </body>
    </html>
  );
}
