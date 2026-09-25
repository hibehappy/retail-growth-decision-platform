import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Retail Growth Decision Platform",
  description:
    "End-to-end retail uplift modeling and decision platform.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
    >
      <body suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
