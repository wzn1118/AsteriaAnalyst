"use client";

import dynamic from "next/dynamic";

import type { SupportedLanguage } from "@/lib/types";

const MonacoEditor = dynamic(() => import("@monaco-editor/react"), {
  ssr: false,
});

export function CodeEditorPanel({
  value,
  language,
  onChange,
}: {
  value: string;
  language: SupportedLanguage;
  onChange: (value: string) => void;
}) {
  return (
    <div className="overflow-hidden rounded-[26px] border border-white/12 bg-[#09111d]">
      <MonacoEditor
        height="360px"
        language={language}
        theme="vs-dark"
        value={value}
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          padding: { top: 18, bottom: 18 },
          scrollBeyondLastLine: false,
          roundedSelection: true,
          tabSize: 2,
          wordWrap: "on",
        }}
        onChange={(nextValue) => onChange(nextValue ?? "")}
      />
    </div>
  );
}
