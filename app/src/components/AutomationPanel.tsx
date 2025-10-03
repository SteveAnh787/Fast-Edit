import { invoke } from "@tauri-apps/api/core";
import { useEffect, useMemo, useState } from "react";
import { pickPath } from "../utils/pickDialog";

type AssetKind = "audio" | "image";

type RenameReport = {
  original: string;
  renamed: string;
  changed: boolean;
};

type WhisperModelInfo = {
  id: string;
  name: string;
  path: string;
  size_bytes: number;
  recommended: boolean;
  available: boolean;
};

type SubtitleBatchReportItem = {
  audioPath: string;
  subtitlePath: string | null;
  previewLines: string[];
};

type StatusMessage = {
  tone: "success" | "error";
  message: string;
};

function basename(path: string) {
  const normalised = path.replace(/\\/g, "/");
  const parts = normalised.split("/");
  return parts[parts.length - 1] ?? path;
}

function formatBytes(bytes: number) {
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const exponent = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / 1024 ** exponent;
  return `${value.toFixed(1)} ${units[exponent]}`;
}

export function AutomationPanel() {
  const [renameKind, setRenameKind] = useState<AssetKind>("audio");
  const [renameDirectory, setRenameDirectory] = useState("");
  const [renamePrefix, setRenamePrefix] = useState("");
  const [renameStartIndex, setRenameStartIndex] = useState("");
  const [renamePadWidth, setRenamePadWidth] = useState("");
  const [renameLowercaseExtension, setRenameLowercaseExtension] = useState(true);
  const [renameBusy, setRenameBusy] = useState(false);
  const [renameStatus, setRenameStatus] = useState<StatusMessage | null>(null);
  const [renameResults, setRenameResults] = useState<RenameReport[]>([]);

  const [audioDirectory, setAudioDirectory] = useState("");
  const [subtitleDirectory, setSubtitleDirectory] = useState("");
  const [language, setLanguage] = useState("");
  const [translateToEnglish, setTranslateToEnglish] = useState(false);
  const [threadCount, setThreadCount] = useState("");
  const [subtitleBusy, setSubtitleBusy] = useState(false);
  const [subtitleStatus, setSubtitleStatus] = useState<StatusMessage | null>(null);
  const [subtitleResults, setSubtitleResults] = useState<SubtitleBatchReportItem[]>([]);
  const [models, setModels] = useState<WhisperModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState("");
  const [modelLoading, setModelLoading] = useState(false);

  const renamedCount = useMemo(
    () => renameResults.filter((item) => item.changed).length,
    [renameResults]
  );

  useEffect(() => {
    let cancelled = false;

    async function loadModels() {
      try {
        setModelLoading(true);
        const result = await invoke<WhisperModelInfo[]>("command_list_models");
        if (cancelled) return;
        setModels(result);
        const recommended = result.find((model) => model.recommended) ?? result[0];
        if (recommended) {
          setSelectedModel(recommended.id);
        }
      } catch (error) {
        console.error(error);
        if (!cancelled) {
          const message = error instanceof Error ? error.message : String(error);
          setSubtitleStatus({ tone: "error", message });
        }
      } finally {
        if (!cancelled) {
          setModelLoading(false);
        }
      }
    }

    loadModels();
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleSelectRenameDirectory() {
    const { path, cancelled } = await pickPath({ kind: "directory" });
    if (path) {
      setRenameDirectory(path);
      setRenameStatus(null);
    } else if (!cancelled) {
      setRenameStatus({ tone: "error", message: "Không thể mở hộp thoại chọn thư mục." });
    }
  }

  async function handleRename() {
    if (!renameDirectory) {
      setRenameStatus({ tone: "error", message: "Vui lòng chọn thư mục trước." });
      return;
    }

    const options: Record<string, unknown> = {};
    if (renamePrefix.trim().length > 0) {
      options.prefix = renamePrefix.trim();
    }
    if (renameStartIndex.trim().length > 0) {
      options.start_index = Number(renameStartIndex.trim());
    }
    if (renamePadWidth.trim().length > 0) {
      options.pad_width = Number(renamePadWidth.trim());
    }
    options.lowercase_extension = renameLowercaseExtension;

    try {
      setRenameBusy(true);
      setRenameStatus(null);
      setRenameResults([]);
      const reports = await invoke<RenameReport[]>("command_batch_rename", {
        directory: renameDirectory,
        kind: renameKind,
        options: Object.keys(options).length > 0 ? options : null,
      });
      setRenameResults(reports);
      setRenameStatus({
        tone: "success",
        message: `Đã xử lý ${reports.length} tệp — đổi tên ${reports.filter((item) => item.changed).length}`,
      });
    } catch (error) {
      console.error(error);
      const message = error instanceof Error ? error.message : String(error);
      setRenameStatus({ tone: "error", message });
    } finally {
      setRenameBusy(false);
    }
  }

  async function handleSelectAudioDirectory() {
    const { path, cancelled } = await pickPath({ kind: "directory" });
    if (path) {
      setAudioDirectory(path);
      setSubtitleStatus(null);
      if (!subtitleDirectory) {
        setSubtitleDirectory(`${path}/subtitles`);
      }
    } else if (!cancelled) {
      setSubtitleStatus({ tone: "error", message: "Không thể mở hộp thoại chọn thư mục audio." });
    }
  }

  async function handleSelectSubtitleDirectory() {
    const { path, cancelled } = await pickPath({ kind: "directory" });
    if (path) {
      setSubtitleDirectory(path);
      setSubtitleStatus(null);
    } else if (!cancelled) {
      setSubtitleStatus({ tone: "error", message: "Không thể mở hộp thoại chọn thư mục phụ đề." });
    }
  }

  async function handleGenerateSubtitles() {
    if (!audioDirectory) {
      setSubtitleStatus({ tone: "error", message: "Cần chọn thư mục audio." });
      return;
    }

    if (!selectedModel) {
      setSubtitleStatus({ tone: "error", message: "Cần chọn model Whisper." });
      return;
    }

    try {
      setSubtitleBusy(true);
      setSubtitleStatus(null);
      setSubtitleResults([]);

      const threads = threadCount.trim().length > 0 ? Number(threadCount.trim()) : null;
      const result = await invoke<{
        audio_path: string;
        subtitle_path: string | null;
        preview_lines: string[];
      }[]>("command_generate_subtitles_batch", {
        args: {
          audioDirectory,
          subtitleDirectory: subtitleDirectory.trim().length > 0 ? subtitleDirectory : null,
          modelId: selectedModel,
          language: language.trim().length > 0 ? language.trim() : null,
          translateToEnglish,
          threads,
        },
      });

      setSubtitleResults(
        result.map((item) => ({
          audioPath: item.audio_path,
          subtitlePath: item.subtitle_path,
          previewLines: item.preview_lines,
        }))
      );
      setSubtitleStatus({
        tone: "success",
        message: `Đã tạo phụ đề cho ${result.length} tệp audio.`,
      });
    } catch (error) {
      console.error(error);
      const message = error instanceof Error ? error.message : String(error);
      setSubtitleStatus({ tone: "error", message });
    } finally {
      setSubtitleBusy(false);
    }
  }

  return (
    <section className="space-y-4">
      <h2 className="text-sm font-semibold uppercase tracking-widest text-slate-400">Tự động hoá quy trình</h2>
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-inner shadow-black/20">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-base font-semibold text-slate-100">Đổi tên thư mục</h3>
            <select
              value={renameKind}
              onChange={(event) => setRenameKind(event.target.value as AssetKind)}
              className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-xs uppercase tracking-wide text-slate-200"
            >
              <option value="audio">Audio</option>
              <option value="image">Image</option>
            </select>
          </div>

          <div className="space-y-3 text-sm text-slate-300">
            <label className="flex flex-col gap-2">
              <span className="text-xs uppercase tracking-wide text-slate-500">Thư mục mục tiêu</span>
              <div className="flex items-center gap-3">
                <input
                  value={renameDirectory}
                  onChange={(event) => setRenameDirectory(event.target.value)}
                  placeholder="Đường dẫn thư mục"
                  className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
                />
                <button
                  onClick={handleSelectRenameDirectory}
                  className="rounded-lg border border-indigo-500/60 bg-indigo-500/20 px-3 py-2 text-xs font-medium uppercase tracking-wide text-indigo-200 transition hover:border-indigo-400 hover:bg-indigo-500/30"
                  type="button"
                >
                  Chọn
                </button>
              </div>
            </label>

            <div className="grid grid-cols-3 gap-3">
              <label className="flex flex-col gap-1">
                <span className="text-xs uppercase tracking-wide text-slate-500">Prefix</span>
                <input
                  value={renamePrefix}
                  onChange={(event) => setRenamePrefix(event.target.value)}
                  placeholder={renameKind === "audio" ? "audio" : "image"}
                  className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
                />
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-xs uppercase tracking-wide text-slate-500">Bắt đầu từ</span>
                <input
                  value={renameStartIndex}
                  onChange={(event) => setRenameStartIndex(event.target.value)}
                  placeholder="1"
                  className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
                />
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-xs uppercase tracking-wide text-slate-500">Pad width</span>
                <input
                  value={renamePadWidth}
                  onChange={(event) => setRenamePadWidth(event.target.value)}
                  placeholder="3"
                  className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
                />
              </label>
            </div>

            <label className="flex items-center gap-2 text-xs uppercase tracking-wide text-slate-500">
              <input
                type="checkbox"
                checked={renameLowercaseExtension}
                onChange={(event) => setRenameLowercaseExtension(event.target.checked)}
                className="h-4 w-4 rounded border border-slate-700 bg-slate-900"
              />
              Tự động viết thường phần mở rộng
            </label>

            <button
              onClick={handleRename}
              disabled={renameBusy}
              className="w-full rounded-lg bg-gradient-to-r from-indigo-500 to-blue-500 px-3 py-2 text-sm font-semibold text-white shadow-lg shadow-indigo-500/30 transition hover:shadow-indigo-500/40 disabled:cursor-not-allowed disabled:opacity-60"
              type="button"
            >
              {renameBusy ? "Đang đổi tên..." : "Đổi tên ngay"}
            </button>

            {renameStatus && (
              <p className={`text-sm ${renameStatus.tone === "success" ? "text-emerald-300" : "text-rose-300"}`}>
                {renameStatus.message}
              </p>
            )}

            {renameResults.length > 0 && (
              <div className="rounded-lg border border-slate-800 bg-slate-900/70 p-3 text-xs text-slate-400">
                <div className="mb-2 font-medium text-slate-200">Xem nhanh ({renamedCount} file đổi tên)</div>
                <ul className="space-y-1">
                  {renameResults
                    .filter((item) => item.changed)
                    .slice(0, 6)
                    .map((item) => (
                      <li key={`${item.original}-${item.renamed}`} className="flex justify-between gap-2">
                        <span className="truncate" title={item.original}>
                          {basename(item.original)}
                        </span>
                        <span className="truncate text-indigo-300" title={item.renamed}>
                          {basename(item.renamed)}
                        </span>
                      </li>
                    ))}
                </ul>
                {renameResults.filter((item) => item.changed).length > 6 && (
                  <div className="pt-1 text-right text-[10px] uppercase tracking-wide text-slate-500">
                    Hiển thị 6 / {renameResults.filter((item) => item.changed).length}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-inner shadow-black/20">
          <h3 className="mb-4 text-base font-semibold text-slate-100">Sinh phụ đề tự động</h3>
          <div className="space-y-3 text-sm text-slate-300">
            <label className="flex flex-col gap-2">
              <span className="text-xs uppercase tracking-wide text-slate-500">Thư mục audio</span>
              <div className="flex items-center gap-3">
                <input
                  value={audioDirectory}
                  onChange={(event) => setAudioDirectory(event.target.value)}
                  placeholder="Đường dẫn thư mục chứa audio (.wav)"
                  className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
                />
                <button
                  onClick={handleSelectAudioDirectory}
                  className="rounded-lg border border-indigo-500/60 bg-indigo-500/20 px-3 py-2 text-xs font-medium uppercase tracking-wide text-indigo-200 transition hover:border-indigo-400 hover:bg-indigo-500/30"
                  type="button"
                >
                  Chọn
                </button>
              </div>
            </label>

            <label className="flex flex-col gap-2">
              <span className="text-xs uppercase tracking-wide text-slate-500">Model Whisper</span>
              <select
                value={selectedModel}
                onChange={(event) => setSelectedModel(event.target.value)}
                disabled={modelLoading || models.length === 0}
                className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {modelLoading && <option>Tải danh sách model...</option>}
                {!modelLoading && models.length === 0 && <option>Không có model khả dụng</option>}
                {!modelLoading &&
                  models.map((model) => (
                    <option key={model.id} value={model.id}>
                      {model.name} · {formatBytes(model.size_bytes)}
                      {model.available ? "" : " · tải khi sử dụng"}
                    </option>
                  ))}
              </select>
              <p className="text-xs text-slate-500">
                Model được lưu cục bộ, tự động tải về nếu chưa có.
              </p>
            </label>

            <label className="flex flex-col gap-2">
              <span className="text-xs uppercase tracking-wide text-slate-500">Thư mục phụ đề</span>
              <div className="flex items-center gap-3">
                <input
                  value={subtitleDirectory}
                  onChange={(event) => setSubtitleDirectory(event.target.value)}
                  placeholder="Mặc định: tạo thư mục subtitles trong audio"
                  className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
                />
                <button
                  onClick={handleSelectSubtitleDirectory}
                  className="rounded-lg border border-indigo-500/60 bg-indigo-500/20 px-3 py-2 text-xs font-medium uppercase tracking-wide text-indigo-200 transition hover:border-indigo-400 hover:bg-indigo-500/30"
                  type="button"
                >
                  Chọn
                </button>
              </div>
            </label>

            <div className="grid grid-cols-3 gap-3">
              <label className="flex flex-col gap-1">
                <span className="text-xs uppercase tracking-wide text-slate-500">Ngôn ngữ</span>
                <input
                  value={language}
                  onChange={(event) => setLanguage(event.target.value)}
                  placeholder="vi, en, ..."
                  className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
                />
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-xs uppercase tracking-wide text-slate-500">Threads</span>
                <input
                  value={threadCount}
                  onChange={(event) => setThreadCount(event.target.value)}
                  placeholder="Tự động"
                  className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
                />
              </label>
              <label className="flex items-center gap-2 text-xs uppercase tracking-wide text-slate-500">
                <input
                  type="checkbox"
                  checked={translateToEnglish}
                  onChange={(event) => setTranslateToEnglish(event.target.checked)}
                  className="h-4 w-4 rounded border border-slate-700 bg-slate-900"
                />
                Dịch sang English
              </label>
            </div>

            <button
              onClick={handleGenerateSubtitles}
              disabled={subtitleBusy || modelLoading}
              className="w-full rounded-lg bg-gradient-to-r from-emerald-500 to-lime-500 px-3 py-2 text-sm font-semibold text-emerald-950 shadow-lg shadow-emerald-500/30 transition hover:shadow-emerald-500/40 disabled:cursor-not-allowed disabled:opacity-60"
              type="button"
            >
              {subtitleBusy ? "Đang xử lý..." : "Tạo phụ đề"}
            </button>

            {subtitleStatus && (
              <p className={`text-sm ${subtitleStatus.tone === "success" ? "text-emerald-300" : "text-rose-300"}`}>
                {subtitleStatus.message}
              </p>
            )}

            {subtitleResults.length > 0 && (
              <div className="rounded-lg border border-slate-800 bg-slate-900/70 p-3 text-xs text-slate-400">
                <div className="mb-2 font-medium text-slate-200">
                  Kết quả ({subtitleResults.length} file)
                </div>
                <ul className="space-y-2 max-h-60 overflow-y-auto pr-2">
                  {subtitleResults.map((item) => (
                    <li key={item.audioPath} className="space-y-1">
                      <div className="flex items-center justify-between text-[11px] uppercase tracking-wide text-slate-500">
                        <span className="truncate" title={item.audioPath}>
                          {basename(item.audioPath)}
                        </span>
                        {item.subtitlePath ? (
                          <span className="truncate text-emerald-300" title={item.subtitlePath}>
                            {basename(item.subtitlePath)}
                          </span>
                        ) : (
                          <span className="text-slate-600">(Không có phụ đề)</span>
                        )}
                      </div>
                      {item.previewLines.length > 0 && (
                        <div className="rounded bg-slate-950/70 px-2 py-1 text-[12px] text-slate-200">
                          {item.previewLines.map((line, index) => (
                            <p key={index} className="truncate" title={line}>
                              {line}
                            </p>
                          ))}
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
