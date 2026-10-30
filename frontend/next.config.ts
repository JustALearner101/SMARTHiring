import fs from "node:fs";
import path from "node:path";
import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

// Load shared monorepo root `.env` automatically if present
const rootEnvPath = path.resolve(__dirname, "..", ".env");
if (fs.existsSync(rootEnvPath) && typeof process.loadEnvFile === "function") {
  process.loadEnvFile(rootEnvPath);
}

const withNextIntl = createNextIntlPlugin();

/**
 * Route prefixes that are temporarily taken out of the app.
 * Page files are intentionally kept in `src/app/[locale]/(admin)/...` so they
 * can be re-enabled later by removing the prefix from this list.
 */
const DISABLED_ROUTE_PREFIXES = ["/simulator", "/audit/guardrail"];

const nextConfig: NextConfig = {
  output: "standalone",
  async redirects() {
    return DISABLED_ROUTE_PREFIXES.flatMap((prefix) => [
      { source: prefix, destination: "/", permanent: false },
      { source: `${prefix}/:path*`, destination: "/", permanent: false },
      { source: `/:locale(en)${prefix}`, destination: "/", permanent: false },
      { source: `/:locale(en)${prefix}/:path*`, destination: "/", permanent: false },
    ]);
  },
  webpack(config) {
    config.module.rules.push({
      test: /\.svg$/,
      use: ["@svgr/webpack"],
    });
    return config;
  },
  images: {
    localPatterns: [
      {
        pathname: "/**",
      },
    ],
  },
  turbopack: {
    root: __dirname,
    rules: {
      "*.svg": {
        loaders: ["@svgr/webpack"],
        as: "*.js",
      },
    },
  },
};

export default withNextIntl(nextConfig);
