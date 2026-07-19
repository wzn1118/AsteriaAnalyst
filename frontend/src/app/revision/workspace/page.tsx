import { Suspense } from "react";

import { RevisionWorkspaceShell } from "@/components/revision-workspace-shell";

export default function RevisionWorkspacePage() {
  return (
    <main className="h-dvh w-full overflow-auto bg-[#08090b] text-white lg:overflow-hidden">
      <Suspense fallback={null}>
        <RevisionWorkspaceShell />
      </Suspense>
    </main>
  );
}
