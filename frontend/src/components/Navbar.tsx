import React from "react";
import { Shield, Trash2, Play, Lock, Zap, Bug } from "lucide-react";
import type { PhoneParseResult } from "../types";

interface NavbarProps {
  currentIdentity: PhoneParseResult | null;
  onLoadDemo: () => void;
  onPurge: () => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

const tabs = [
  { id: "scan", label: "Scan & Dorks", icon: Bug },
  { id: "exposures", label: "Exposures", icon: Zap },
  { id: "remediation", label: "Remediation Hub", icon: Shield },
  { id: "prevention", label: "Spam & DND", icon: Lock },
  { id: "audit", label: "Verify & Audit", icon: Trash2 },
] as const;

export const Navbar: React.FC<NavbarProps> = ({
  currentIdentity,
  onLoadDemo,
  onPurge,
  activeTab,
  setActiveTab,
}) => {
  return (
    <header className="border-b border-[var(--border-subtle)] bg-[var(--bg-surface)]/90 backdrop-blur-md sticky top-0 z-40">
      <div className="container-shell flex items-center justify-between gap-4 h-16">
        {/* Brand */}
        <button type="button" className="flex items-center gap-3 shrink-0 text-left" onClick={() => setActiveTab("scan")}>
          <div className="w-9 h-9 rounded-lg bg-sky-950/80 border border-sky-800 flex items-center justify-center text-sky-400 shadow-sm">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-1.5 sm:gap-2">
              <span className="brand-title">ClearNum</span>
              <span className="font-mono text-xs text-slate-300 font-semibold tracking-tight">NumberShield</span>
              <span className="kicker-tag text-[10px]">v1.0 Local</span>
            </div>
            <p className="hidden xl:block text-xs text-[var(--text-dim)]">Open-source phone privacy & remediation</p>
          </div>
        </button>

        {/* Navigation Tabs */}
        <nav aria-label="Main" className="hidden lg:flex items-center gap-1 bg-[var(--bg-app)] p-1 rounded-xl border border-[var(--border-subtle)]">
          {[
            { id: "scan", label: "Scan & Dorks" },
            { id: "exposures", label: "Exposures" },
            { id: "remediation", label: "Remediation Hub" },
            { id: "prevention", label: "Spam & DND" },
            { id: "audit", label: "Verify & Audit" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              aria-current={activeTab === tab.id ? "page" : undefined}
              className={`px-3.5 py-1.5 rounded-lg text-[13px] font-semibold whitespace-nowrap transition-colors ${
                activeTab === tab.id
                  ? "bg-[var(--bg-elevated)] text-sky-300 shadow-sm ring-1 ring-[var(--border-strong)]"
                  : "text-[var(--text-muted)] hover:text-slate-100 hover:bg-[var(--bg-card)]"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        {/* Identity & Actions */}
        <div className="flex items-center gap-2 shrink-0">
          {currentIdentity ? (
            <div className="hidden 2xl:flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border-subtle)] text-xs whitespace-nowrap" title="Current number (masked)">
              <Lock className="w-3.5 h-3.5 text-emerald-400" />
              <span className="font-mono text-slate-200">{currentIdentity.masked_display}</span>
              
            </div>
          ) : null}

          <button
            onClick={onLoadDemo}
            className="btn btn-secondary text-xs py-1.5 px-2.5 sm:px-3 shrink-0"
            title="Load synthetic scenario with realistic data brokers and spam reports"
          >
            <Play className="w-3.5 h-3.5 text-sky-400" />
            <span className="hidden xl:inline">Load Demo</span>
          </button>

          <button
            onClick={onPurge}
            className="btn btn-pixel danger text-xs py-1.5 px-2.5 sm:px-3 shrink-0"
            title="Zero-trace cryptographic wipe of all local records"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span className="hidden xl:inline">Purge</span>
          </button>
        </div>

      {/* Mobile Sub-Navigation Bar */}
      <nav aria-label="Main" className="flex lg:hidden border-t border-[var(--border-subtle)] px-3 py-2 overflow-x-auto gap-1.5 bg-[var(--bg-app)]/80">
        {[
          { id: "scan", label: "Scan & Dorks" },
          { id: "exposures", label: "Exposures" },
          { id: "remediation", label: "Remediation Hub" },
          { id: "prevention", label: "Spam & DND" },
          { id: "audit", label: "Verify & Audit" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            aria-current={activeTab === tab.id ? "page" : undefined}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors ${
              activeTab === tab.id
                ? "bg-[var(--bg-elevated)] text-sky-400 border border-[var(--border-strong)]"
                : "text-[var(--text-muted)]"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </nav>
    </header>
  );
};

export default Navbar;
