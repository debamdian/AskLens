import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";

describe("AskLens Frontend Smoke Tests", () => {
  it("contains required Next.js App Router pages and Auth.js route", () => {
    const requiredFiles = [
      "app/page.tsx",
      "app/layout.tsx",
      "app/admin/page.tsx",
      "app/api/auth/[...nextauth]/route.ts",
      "auth.ts",
      "components/chat/ChatFeed.tsx",
      "components/chat/ChartRenderer.tsx",
      "components/voice/VoiceModal.tsx",
    ];
    for (const rel of requiredFiles) {
      const fullPath = path.resolve(__dirname, "..", rel);
      expect(fs.existsSync(fullPath), `Missing file: ${rel}`).toBe(true);
    }
  });

  it("configures TypeScript strict mode", () => {
    const tsconfigPath = path.resolve(__dirname, "..", "tsconfig.json");
    const raw = fs.readFileSync(tsconfigPath, "utf-8");
    const parsed = JSON.parse(raw);
    expect(parsed.compilerOptions.strict).toBe(true);
  });
});
