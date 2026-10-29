import { AuthProvider } from "@/context/AuthContext";
import { QueryProvider } from "@/context/QueryProvider";
import { SidebarProvider } from "@/context/SidebarContext";
import { ThemeProvider } from "@/context/ThemeContext";
import { ToastProvider } from "@/context/ToastContext";
import { isRtl } from "@/i18n/languages";
import { type Locale, routing } from "@/i18n/routing";
import "flatpickr/dist/flatpickr.css";
import { NextIntlClientProvider } from "next-intl";
import { setRequestLocale } from "next-intl/server";
import { Plus_Jakarta_Sans, Poppins } from "next/font/google";
import { notFound } from "next/navigation";
import "simplebar-react/dist/simplebar.min.css";
import "swiper/css/bundle";
import "../globals.css";

const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-sans",
});

const poppins = Poppins({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-poppins",
});

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export default async function RootLayout({
  children,
  params,
}: Readonly<{
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}>) {
  const { locale } = await params;

  if (!routing.locales.includes(locale as Locale)) {
    notFound();
  }

  setRequestLocale(locale);

  return (
    <html lang={locale} dir={isRtl(locale as Locale) ? "rtl" : "ltr"} suppressHydrationWarning>
      <body suppressHydrationWarning className={`${poppins.className} dark:bg-gray-900`}>
        <NextIntlClientProvider>
          <QueryProvider>
            <ThemeProvider>
              <SidebarProvider>
                <AuthProvider>
                  <ToastProvider>{children}</ToastProvider>
                </AuthProvider>
              </SidebarProvider>
            </ThemeProvider>
          </QueryProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
