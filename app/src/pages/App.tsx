import { SceneListPanel } from "../components/SceneListPanel";
import { SubtitlePanel } from "../components/SubtitlePanel";
import { SystemStatusBar } from "../components/SystemStatusBar";

export function App() {
  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-transparent p-6">
      <div className="flex h-[720px] w-full max-w-6xl overflow-hidden rounded-3xl bg-slate-950/80 backdrop-blur-xl shadow-[0_40px_120px_rgba(15,23,42,0.45)] ring-1 ring-white/5">
        <SceneListPanel />
        <div className="flex flex-1 flex-col">
          <SubtitlePanel />
          <SystemStatusBar />
        </div>
      </div>
    </div>
  );
}
