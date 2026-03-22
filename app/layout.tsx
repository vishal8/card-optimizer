import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Card Optimizer",
  description: "Credit card optimizer and comparator"
};

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}