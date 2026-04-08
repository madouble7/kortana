import { Activity, CheckCircle2, ChevronDown, ChevronRight, Shield, XCircle } from 'lucide-react';
import React, { useState } from 'react';
import { cn } from '../lib/utils';
import type { SandboxResult } from '../types';

interface Props {
  result: SandboxResult;
}

function ExpandableSection({ title, children, defaultOpen = false }: { title: string, children: React.ReactNode, defaultOpen?: boolean }) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="border border-gray-700/50 rounded-md overflow-hidden mt-2">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-3 py-2 bg-gray-800/50 hover:bg-gray-700/50 transition-colors text-sm font-medium text-gray-300"
      >
        {title}
        {isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
      </button>
      {isOpen && (
        <div className="p-3 bg-gray-900/50 text-xs text-gray-300 overflow-x-auto">
          {children}
        </div>
      )}
    </div>
  );
}

export default function SandboxResultView({ result }: Props) {
  const isOk = result.ok;

  return (
    <div className="mt-3 p-3 rounded-lg border border-indigo-900/30 bg-gray-800/30">
      <div className="flex items-center justify-between mb-3 text-sm">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-indigo-400" />
          <span className="font-semibold text-indigo-300">Shadow Bridge Trace</span>
        </div>
        <div className="flex items-center gap-2">
          {isOk ? (
            <span className="flex items-center gap-1 text-green-400 bg-green-400/10 px-2 py-0.5 rounded">
              <CheckCircle2 className="w-3 h-3" /> {result.status || 'passed'}
            </span>
          ) : (
            <span className="flex items-center gap-1 text-red-400 bg-red-400/10 px-2 py-0.5 rounded">
              <XCircle className="w-3 h-3" /> {result.status || 'failed'}
            </span>
          )}
        </div>
      </div>

      {result.error && (
        <div className="text-red-400 text-xs mb-3 p-2 bg-red-400/10 rounded">
          {result.error}
        </div>
      )}

      {result.artifacts && (
        <div className="space-y-3">
          {/* Top-level vital signs */}
          <div className="flex flex-wrap gap-2 text-xs">
            {result.artifacts.plan?.risk_assessment && (
              <span className="flex items-center gap-1 px-2 py-1 rounded bg-gray-800 border border-gray-700">
                <Shield className="w-3 h-3 text-orange-400" />
                Risk: {result.artifacts.plan.risk_assessment}
              </span>
            )}

            {result.artifacts.review_summary !== undefined && (
              <span className={cn(
                "flex items-center gap-1 px-2 py-1 rounded border",
                result.artifacts.review_summary.approved
                  ? "bg-green-900/20 border-green-800 text-green-400"
                  : "bg-red-900/20 border-red-800 text-red-400"
              )}>
                Review: {result.artifacts.review_summary.approved ? 'Approved' : 'Rejected'}
              </span>
            )}

            {result.artifacts.test_report?.exit_code !== undefined && (
              <span className={cn(
                "flex items-center gap-1 px-2 py-1 rounded border",
                result.artifacts.test_report.exit_code === 0
                  ? "bg-green-900/20 border-green-800 text-green-400"
                  : "bg-red-900/20 border-red-800 text-red-400"
              )}>
                Tests: Exit {result.artifacts.test_report.exit_code}
              </span>
            )}

            {result.artifacts.deployment_manifest !== undefined && (
              <span className="flex items-center gap-1 px-2 py-1 rounded bg-gray-800 border border-gray-700">
                Dry Run: {result.artifacts.deployment_manifest.dryRun ? 'Yes' : 'No'}
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 gap-1">
            {result.artifacts.plan && (
              <ExpandableSection title="Precognitive Plan">
                <pre className="whitespace-pre-wrap font-mono">{JSON.stringify(result.artifacts.plan, null, 2)}</pre>
              </ExpandableSection>
            )}

            {result.artifacts.changeset && (
              <ExpandableSection title="Proposed Changeset">
                <pre className="whitespace-pre-wrap font-mono">{JSON.stringify(result.artifacts.changeset, null, 2)}</pre>
              </ExpandableSection>
            )}

            {result.artifacts.test_report && (
              <ExpandableSection title="Diagnostic Test Report">
                <pre className="whitespace-pre-wrap font-mono">{JSON.stringify(result.artifacts.test_report, null, 2)}</pre>
              </ExpandableSection>
            )}

            {result.artifacts.review_summary && (
              <ExpandableSection title="Review Summary">
                <pre className="whitespace-pre-wrap font-mono">{JSON.stringify(result.artifacts.review_summary, null, 2)}</pre>
              </ExpandableSection>
            )}

            {result.artifacts.deployment_manifest && (
              <ExpandableSection title="Deployment Manifest">
                <pre className="whitespace-pre-wrap font-mono">{JSON.stringify(result.artifacts.deployment_manifest, null, 2)}</pre>
              </ExpandableSection>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

