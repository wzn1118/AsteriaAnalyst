"use client";

import { useEffect, useState } from "react";

import { ReportRevisionWorkbench } from "@/components/report-revision-workbench";

function isRevisionRoute() {
  if (typeof window === "undefined") {
    return false;
  }
  const params = new URLSearchParams(window.location.search);
  return params.get("mode") === "revision" || window.location.hash === "#revision";
}

export function RevisionRouteGate() {
  const [isRevision, setIsRevision] = useState(false);

  useEffect(() => {
    const syncRouteMode = () => {
      setIsRevision(isRevisionRoute());
    };

    syncRouteMode();
    window.addEventListener("popstate", syncRouteMode);
    window.addEventListener("hashchange", syncRouteMode);
    return () => {
      window.removeEventListener("popstate", syncRouteMode);
      window.removeEventListener("hashchange", syncRouteMode);
    };
  }, []);

  if (!isRevision) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-[1000] overflow-y-auto bg-[#080b10] px-4 py-6 text-white sm:px-6 lg:px-8">
      <div className="mx-auto max-w-[1800px]">
        <ReportRevisionWorkbench
          onBack={() => {
            window.history.replaceState(null, "", window.location.pathname);
            setIsRevision(false);
          }}
        />
      </div>
    </div>
  );
}
