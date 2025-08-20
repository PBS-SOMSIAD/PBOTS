import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { KeycloakProvider } from "./contexts/KeycloakContext";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: "D&D Agent",
  description: "Ask questions about Dungeons & Dragons 5th Edition",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        <KeycloakProvider>
          {children}
        </KeycloakProvider>
      </body>
    </html>
  );
}
