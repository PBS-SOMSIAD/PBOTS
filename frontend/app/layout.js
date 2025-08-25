import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

// Konfiguracja czcionek 
const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

//Metadane strony
export const metadata = {
  title: "PBOTS",
  description: "Asystent PBOTS",
};

//Definicja układu strony
export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        {children}
      </body>
    </html>
  );
}
