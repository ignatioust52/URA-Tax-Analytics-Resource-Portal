import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "URA Revenue Dashboard",
  description: "DEVELOPING UGANDA TOGETHER",
  icons: {
    icon: '/logo.png',
  },
};

import { Providers } from "./Providers";
import { TopNav } from "../components/TopNav";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <TopNav />
          {children}
        </Providers>
      </body>
    </html>
  );
}
