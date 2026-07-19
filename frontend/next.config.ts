import type { NextConfig } from "next";

const isStaticExport = process.env.BUILD_MODE === "export";
const codexDistDir = process.env.CODEX_NEXT_DIST_DIR?.trim();

const nextConfig: NextConfig = {
  distDir: codexDistDir || undefined,
  output: isStaticExport ? "export" : undefined,
  allowedDevOrigins: ["127.0.0.1"],
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
