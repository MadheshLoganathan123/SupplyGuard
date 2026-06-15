import type { NextConfig } from "next";
import { join } from "path";

const nextConfig: NextConfig = {
  /* config options here */
  // When multiple package-lock files exist in parent folders Next warns.
  // Point `outputFileTracingRoot` at the monorepo/workspace root to silence warning.
  outputFileTracingRoot: join(__dirname, ".."),
};

export default nextConfig;
