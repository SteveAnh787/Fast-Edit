import { useSystemStatus } from "../hooks/useSystemStatus";

export function SystemStatusBar() {
  const status = useSystemStatus();

  return (
    <footer className="grid grid-cols-3 gap-4 border-t border-slate-800 bg-slate-900/80 p-3 text-xs text-slate-400">
      <div>
        <span className="font-semibold text-slate-200">CPU:</span>{" "}
        {status ? `${status.cpu_usage.toFixed(1)}%` : "--"}
      </div>
      <div>
        <span className="font-semibold text-slate-200">RAM:</span>{" "}
        {status
          ? `${(status.memory_used_mb / 1024).toFixed(1)} / ${(status.memory_total_mb / 1024).toFixed(1)} GB`
          : "--"}
      </div>
      <div>
        <span className="font-semibold text-slate-200">Proc:</span>{" "}
        {status ? status.process_count : "--"}
      </div>
    </footer>
  );
}
