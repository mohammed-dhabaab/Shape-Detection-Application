import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import type { ReactNode } from "react";

import { appMetadata, appViewport } from "@/app";

import "@/app/styles/globals.css";

// Next.js routing lives in this root `app/` directory and stays thin; the application
// itself is organised with Feature-Sliced Design under `src/` (see README).

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = appMetadata;
export const viewport: Viewport = appViewport;

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable}`}>
      <body className="font-sans">{children}</body>
    </html>
  );
}
