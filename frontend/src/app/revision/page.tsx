import { Suspense } from "react";

import { RevisionModeShell } from "@/components/revision-mode-shell";

export default function RevisionPage() {
  return (
    <main className="h-dvh w-full overflow-auto bg-[#08090b] text-white lg:overflow-hidden">
      <Suspense fallback={null}>
        <RevisionModeShell />
      </Suspense>
    </main>
  );
}
