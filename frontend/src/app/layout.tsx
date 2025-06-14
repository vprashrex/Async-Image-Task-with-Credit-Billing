import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/contexts/AuthContext";
import { Toaster } from "@/components/ui/sonner";
import ErrorBoundary from "@/components/ErrorBoundary";
import { SkipLink } from "@/components/SkipLink";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Virtual Space Tech - Image Processing SaaS",
  description: "Professional async image processing with AI-powered enhancements",
  keywords: ["image processing", "AI", "saas", "async", "upload"],
  authors: [{ name: "Virtual Space Tech" }],
  creator: "Virtual Space Tech",
  publisher: "Virtual Space Tech",
  robots: {
    index: true,
    follow: true,
  },
  manifest: "/manifest.json",
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://virtualspacetech.com",
    title: "Virtual Space Tech - Image Processing SaaS",
    description: "Professional async image processing with AI-powered enhancements",
    siteName: "Virtual Space Tech",
  },
  twitter: {
    card: "summary_large_image",
    title: "Virtual Space Tech - Image Processing SaaS",
    description: "Professional async image processing with AI-powered enhancements",
    creator: "@virtualspacetech",
  },
  viewport: {
    width: "device-width",
    initialScale: 1,
    maximumScale: 1,
  },
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#000000" },
  ],
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "Virtual Space Tech",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <SkipLink />
        <ErrorBoundary>
          <AuthProvider>
            <main id="main-content">
              {children}
            </main>
            <Toaster />
          </AuthProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
