import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
    title: "Veriply - Trust-First AI Customer Service",
    description:
        "Human-in-the-loop verification for AI-generated customer support responses",
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en">
            <body className="antialiased" suppressHydrationWarning>
                <Providers>{children}</Providers>
            </body>
        </html>
    );
}
