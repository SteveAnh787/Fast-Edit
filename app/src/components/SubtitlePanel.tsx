import { useProject } from "../state/useProject";
import { useState } from "react";
import { AutomationPanel } from "./AutomationPanel";
import { ComposerPanel } from "./ComposerPanel";

type TabKey = "automation" | "composer";

export function SubtitlePanel() {
  const style = useProject((state) => state.project.subtitle_style);
  const [previewText, setPreviewText] = useState("");
  const [activeTab, setActiveTab] = useState<TabKey>("automation");

  return (
    <section className="flex flex-1 flex-col">
      <nav className="flex gap-2 border-b border-slate-800 bg-slate-950/60 px-6 pt-6">
        <TabButton
          label="Tự động hoá"
          active={activeTab === "automation"}
          onClick={() => setActiveTab("automation")}
        />
        <TabButton
          label="Ghép & render"
          active={activeTab === "composer"}
          onClick={() => setActiveTab("composer")}
        />
      </nav>

      <div className="flex-1 overflow-y-auto">
        {activeTab === "automation" ? (
          <AutomationTab
            styleFont={style.font_family}
            styleSize={style.font_size}
            previewText={previewText}
            onChangePreview={setPreviewText}
          />
        ) : (
          <ComposerPanel />
        )}
      </div>
    </section>
  );
}

type AutomationTabProps = {
  styleFont: string;
  styleSize: number;
  previewText: string;
  onChangePreview: (value: string) => void;
};

function AutomationTab({ styleFont, styleSize, previewText, onChangePreview }: AutomationTabProps) {
  return (
    <div className="flex flex-col gap-6 overflow-y-auto p-6">
      <div className="flex flex-col gap-6 lg:flex-row">
        <div className="w-full max-w-xs space-y-4">
          <h2 className="text-sm font-semibold uppercase tracking-widest text-slate-400">Phụ đề nâng cao</h2>
          <div className="space-y-3 text-sm text-slate-300">
            <label className="flex flex-col gap-1">
              <span className="text-xs uppercase tracking-wide text-slate-500">Font</span>
              <select className="rounded border border-slate-700 bg-slate-900 p-2 text-slate-100" defaultValue={styleFont}>
                <option>Arial</option>
                <option>Helvetica</option>
                <option>Montserrat</option>
              </select>
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-xs uppercase tracking-wide text-slate-500">Size</span>
              <input type="number" defaultValue={styleSize} className="rounded border border-slate-700 bg-slate-900 p-2" />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-xs uppercase tracking-wide text-slate-500">Màu chữ</span>
              <input type="color" defaultValue="#ffffff" className="h-10 w-full rounded border border-slate-700 bg-slate-900" />
            </label>
          </div>
        </div>

        <div className="flex flex-1 flex-col gap-4">
          <div className="flex-1 rounded-xl border border-slate-800 bg-black/90 p-6 shadow-[inset_0_0_40px_rgba(0,0,0,0.6)]">
            <div className="flex h-full items-center justify-center">
              <p
                className="text-xl font-semibold text-yellow-300 drop-shadow"
                style={{
                  fontFamily: styleFont,
                  fontSize: `${styleSize}px`,
                }}
              >
                {previewText || "Nhập nội dung để xem preview"}
              </p>
            </div>
          </div>
          <input
            value={previewText}
            placeholder="Gõ nội dung phụ đề mẫu..."
            onChange={(event) => onChangePreview(event.target.value)}
            className="rounded-lg border border-slate-700 bg-slate-900 p-3 text-slate-100"
          />
        </div>
      </div>

      <AutomationPanel />
    </div>
  );
}

type TabButtonProps = {
  label: string;
  active: boolean;
  onClick: () => void;
};

function TabButton({ label, active, onClick }: TabButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-t-lg px-4 py-2 text-sm font-semibold uppercase tracking-wide transition ${
        active
          ? "border-b-2 border-indigo-400 text-slate-100"
          : "text-slate-500 hover:text-slate-200"
      }`}
    >
      {label}
    </button>
  );
}
