import { useProject } from "../state/useProject";

export function SceneListPanel() {
  const scenes = useProject((state) => state.project.scenes);

  return (
    <aside className="w-72 border-r border-slate-800 bg-slate-900/60 backdrop-blur">
      <header className="p-4 text-lg font-semibold uppercase tracking-widest text-slate-400">
        Danh sách cảnh
      </header>
      <div className="space-y-2 overflow-y-auto p-4">
        {scenes.map((scene) => (
          <div
            key={scene.id}
            className="rounded-lg border border-slate-800 bg-slate-800/60 p-3 transition hover:border-indigo-500 hover:shadow"
          >
            <div className="font-medium text-slate-100">{scene.id}</div>
            <div className="text-xs text-slate-400">
              {scene.media.type === "Image" ? "Hình ảnh" : "Video"} · {scene.duration_secs.toFixed(1)}s
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}
