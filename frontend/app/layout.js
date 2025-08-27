import './globals.css';
import { Saira } from 'next/font/google';

const saira = Saira({
  subsets: ['latin'],
  display: 'swap',
  weight: ['400', '700'],
});

export const metadata = {
  title: "PBOTS",
  description: "Asystent PBOTS",
};

export default function RootLayout({ children }) {
  return (
    <html lang="pl" className={saira.className}>
      <body>{children}</body>
    </html>
  );
}
