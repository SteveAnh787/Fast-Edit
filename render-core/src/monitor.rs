use serde::Serialize;
use sysinfo::{CpuExt, System, SystemExt};

#[derive(Debug, Clone, Serialize)]
pub struct SystemStatus {
    pub cpu_usage: f32,
    pub memory_used_mb: f32,
    pub memory_total_mb: f32,
    pub process_count: usize,
}

impl SystemStatus {
    pub fn gather() -> Self {
        let mut system = System::new_all();
        system.refresh_all();

        let cpu_usage = system
            .cpus()
            .iter()
            .map(|cpu| cpu.cpu_usage() as f32)
            .sum::<f32>()
            / system.cpus().len().max(1) as f32;

        let memory_total_mb = system.total_memory() as f32 / 1024.0;
        let memory_used_mb = system.used_memory() as f32 / 1024.0;

        Self {
            cpu_usage,
            memory_used_mb,
            memory_total_mb,
            process_count: system.processes().len(),
        }
    }
}
