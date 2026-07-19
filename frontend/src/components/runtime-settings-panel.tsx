"use client";

import { LockKeyhole, ShieldCheck } from "lucide-react";

export function RuntimeSettingsPanel() {
  return (
    <section className="elevated-panel p-6 md:p-7">
      <div className="section-header">
        <div className="section-badge bg-[rgba(46,86,49,0.34)]">
          <LockKeyhole size={18} />
        </div>
        <div>
          <p className="section-kicker">Release Configuration</p>
          <h2 className="section-title">Server-managed runtime settings</h2>
        </div>
      </div>

      <div className="runtime-status-card mt-5">
        <div className="flex items-start gap-3">
          <div className="icon-plate shrink-0">
            <ShieldCheck size={18} />
          </div>
          <div>
            <p className="text-sm font-semibold text-[var(--text-strong)]">
              Public release protection
            </p>
            <p className="mt-2 text-sm leading-7 text-[var(--muted)]">
              API credentials, providers, and execution paths are configured with server environment variables. This public build does not expose browser-side runtime settings.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
