import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "IndraStra Harvester — Scholarly Discovery",
    template: "%s | IndraStra Harvester",
  },
  description: "Discover scholarly metadata from repositories and research collections.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <header className="site-header">
          <div className="header-inner">
            <Link className="brand" href="/">
              <span className="brand-mark">IH</span>
              <span>
                <strong>IndraStra Harvester</strong>
                <small>Scholarly discovery</small>
              </span>
            </Link>
            <nav aria-label="Main navigation">
              <Link href="/">Search</Link>
              <Link href="/admin">Administration</Link>
            </nav>
          </div>
        </header>
        <main>{children}</main>
        <footer className="site-footer">
          <div className="footer-inner">
            <span>IndraStra Harvester</span>
            <span>Open scholarly metadata discovery · AGPL-3.0</span>
          </div>
        </footer>
      </body>
    </html>
  );
}
