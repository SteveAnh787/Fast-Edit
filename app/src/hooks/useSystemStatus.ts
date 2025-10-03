import { useEffect, useState } from "react";
import { invoke } from "@tauri-apps/api/core";

type SystemStatus = {
  cpu_usage: number;
  memory_used_mb: number;
  memory_total_mb: number;
  process_count: number;
};

export function useSystemStatus() {
  const [status, setStatus] = useState<SystemStatus | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function tick() {
      try {
        const payload = await invoke<string>("command_system_status");
        const parsed = JSON.parse(payload) as SystemStatus;
        if (!cancelled) {
          setStatus(parsed);
        }
      } catch (error) {
        console.error("Failed to capture system status", error);
      }
    }

    tick();
    const interval = setInterval(tick, 1500);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return status;
}
