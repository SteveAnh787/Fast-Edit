import { invoke } from "@tauri-apps/api/core";
import { useMemo, useState } from "react";
import { pickPath, PickDialogKind, PickDialogOptions } from "../utils/pickDialog";

type StitchReportItem = {
  index: number;
  audio_path: string;
  image_path: string;
  subtitle_path?: string | null;
  output_path: string;
};

type StatusMessage = {
  tone: "success" | "error";
  message: string;
};

const VIDEO_CODEC_OPTIONS = [
  { id: "h264", label: "H.264 (VideoToolbox)" },
  { id: "hevc", label: "HEVC H.265 (VideoToolbox)" },
];

const FONT_OPTIONS = ["Arial", "Helvetica", "Montserrat", "Roboto", "Open Sans", "Inter"];

type ComposerPanelProps = {
  fontFamily: string;
  setFontFamily: (value: string) => void;
  fontSize: number;
  setFontSize: (value: number) => void;
  textColor: string;
  setTextColor: (value: string) => void;
  outlineColor: string;
  setOutlineColor: (value: string) => void;
  outlineWidth: number;
  setOutlineWidth: (value: number) => void;
  letterSpacing: number;
  setLetterSpacing: (value: number) => void;
  previewText: string;
  setPreviewText: (value: string) => void;
};

export function ComposerPanel({
  fontFamily,
  setFontFamily,
  fontSize,
  setFontSize,
  textColor,
  setTextColor,
  outlineColor,
  setOutlineColor,
  outlineWidth,
  setOutlineWidth,
  letterSpacing,
  setLetterSpacing,
  previewText,
  setPreviewText,
}: ComposerPanelProps) {
  const [audioDirectory, setAudioDirectory] = useState("");
  const [imageDirectory, setImageDirectory] = useState("");
  const [subtitleDirectory, setSubtitleDirectory] = useState("");
  const [outputDirectory, setOutputDirectory] = useState("");
  const [frameRate, setFrameRate] = useState("30");
  const [videoCodec, setVideoCodec] = useState("h264");
  const [audioBitrate, setAudioBitrate] = useState("192k");
  const [burnSubtitles, setBurnSubtitles] = useState(false);

  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<StatusMessage | null>(null);
  const [results, setResults] = useState<StitchReportItem[]>([]);

  const handleSelectDirectory = async (
    setter: (value: string) => void,
    kind: PickDialogKind,
    options: Partial<PickDialogOptions> = {}
  ) => {
    const result = await pickPath({ kind, ...options });
    if (result.path) {
      setter(result.path);
      setStatus(null);
    } else if (!result.cancelled) {
      setStatus({ tone: "error", message: "Không thể mở hộp thoại." });
    }
  };

  const handleCompose = async () => {
    if (!audioDirectory || !imageDirectory || !outputDirectory) {
      setStatus({
        tone: "error",
        message: "Cần chọn thư mục audio, hình ảnh và thư mục xuất video.",
      });
      return;
    }

    const parsedFrameRate = Number(frameRate);
    if (Number.isNaN(parsedFrameRate) || parsedFrameRate <= 0) {
      setStatus({ tone: "error", message: "Frame rate không hợp lệ." });
      return;
    }

    try {
      setBusy(true);
      setStatus(null);
      setResults([]);

      const subtitleStyle = {
        fontName: fontFamily,
        fontSize: Number.isFinite(fontSize) && fontSize > 0 ? fontSize : undefined,
        primaryColor: textColor,
        outlineColor,
        outlineWidth: Number.isFinite(outlineWidth) && outlineWidth >= 0 ? outlineWidth : undefined,
        letterSpacing:
          Number.isFinite(letterSpacing) && letterSpacing !== 0 ? letterSpacing : undefined,
      };

      const response = await invoke<StitchReportItem[]>("command_stitch_assets", {
        args: {
          audioDirectory,
          imageDirectory,
          subtitleDirectory: subtitleDirectory.trim().length > 0 ? subtitleDirectory : null,
          outputDirectory,
          frameRate: parsedFrameRate,
          codec: videoCodec,
          audioBitrate: audioBitrate.trim().length > 0 ? audioBitrate : "192k",
          burnSubtitles,
          subtitleStyle,
        },
      });

      setResults(response);
      if (response.length > 0) {
        const first = response[0];
        const location = basename(first.output_path.replace(/\\\\/g, "/"));
        setStatus({
          tone: "success",
          message: `Đã render ${response.length} video · Ví dụ: ${location}`,
        });
      } else {
        setStatus({ tone: "success", message: "Không có video nào được ghép." });
      }
    } catch (error) {
      console.error(error);
      const message = error instanceof Error ? error.message : String(error);
      setStatus({ tone: "error", message });
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="space-y-4 p-6">
      <h2 className="text-sm font-semibold uppercase tracking-widest text-slate-400">
        Ghép nội dung & render
      </h2>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-3 text-sm text-slate-300">
          <label className="flex flex-col gap-2">
            <span className="text-xs uppercase tracking-wide text-slate-500">
              Thư mục audio
            </span>
            <div className="flex items-center gap-3">
              <input
                value={audioDirectory}
                onChange={(event) => setAudioDirectory(event.target.value)}
                placeholder="Đường dẫn thư mục audio"
                className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
              />
              <button
                onClick={() => handleSelectDirectory(setAudioDirectory, "directory")}
                className="rounded-lg border border-indigo-500/60 bg-indigo-500/20 px-3 py-2 text-xs font-medium uppercase tracking-wide text-indigo-200 transition hover:border-indigo-400 hover:bg-indigo-500/30"
                type="button"
              >
                Chọn
              </button>
            </div>
          </label>

          <label className="flex flex-col gap-2">
            <span className="text-xs uppercase tracking-wide text-slate-500">
              Thư mục hình ảnh
            </span>
            <div className="flex items-center gap-3">
              <input
                value={imageDirectory}
                onChange={(event) => setImageDirectory(event.target.value)}
                placeholder="Đường dẫn thư mục hình ảnh"
                className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
              />
              <button
                onClick={() => handleSelectDirectory(setImageDirectory, "directory")}
                className="rounded-lg border border-indigo-500/60 bg-indigo-500/20 px-3 py-2 text-xs font-medium uppercase tracking-wide text-indigo-200 transition hover:border-indigo-400 hover:bg-indigo-500/30"
                type="button"
              >
                Chọn
              </button>
            </div>
          </label>

          <label className="flex flex-col gap-2">
            <span className="text-xs uppercase tracking-wide text-slate-500">
              Thư mục phụ đề (tuỳ chọn)
            </span>
            <div className="flex items-center gap-3">
              <input
                value={subtitleDirectory}
                onChange={(event) => setSubtitleDirectory(event.target.value)}
                placeholder="Đường dẫn thư mục phụ đề .srt"
                className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
              />
              <button
                onClick={() => handleSelectDirectory(setSubtitleDirectory, "directory")}
                className="rounded-lg border border-indigo-500/60 bg-indigo-500/20 px-3 py-2 text-xs font-medium uppercase tracking-wide text-indigo-200 transition hover:border-indigo-400 hover:bg-indigo-500/30"
                type="button"
              >
                Chọn
              </button>
            </div>
          </label>

          <label className="flex flex-col gap-2">
            <span className="text-xs uppercase tracking-wide text-slate-500">
              Thư mục xuất video
            </span>
            <div className="flex items-center gap-3">
              <input
                value={outputDirectory}
                onChange={(event) => setOutputDirectory(event.target.value)}
                placeholder="Đường dẫn lưu video (.mp4)"
                className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
              />
              <button
                onClick={() =>
                  handleSelectDirectory(setOutputDirectory, "directory", { title: "Chọn thư mục xuất" })
                }
                className="rounded-lg border border-indigo-500/60 bg-indigo-500/20 px-3 py-2 text-xs font-medium uppercase tracking-wide text-indigo-200 transition hover:border-indigo-400 hover:bg-indigo-500/30"
                type="button"
              >
                Chọn
              </button>
            </div>
          </label>
        </div>

        <div className="space-y-3 text-sm text-slate-300">
          <label className="flex flex-col gap-1">
            <span className="text-xs uppercase tracking-wide text-slate-500">Frame rate</span>
            <input
              value={frameRate}
              onChange={(event) => setFrameRate(event.target.value)}
              placeholder="30"
              className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
            />
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-xs uppercase tracking-wide text-slate-500">Video codec</span>
            <select
              value={videoCodec}
              onChange={(event) => setVideoCodec(event.target.value)}
              className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
            >
              {VIDEO_CODEC_OPTIONS.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-xs uppercase tracking-wide text-slate-500">Audio bitrate</span>
            <input
              value={audioBitrate}
              onChange={(event) => setAudioBitrate(event.target.value)}
              placeholder="192k"
              className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
            />
          </label>

          <label className="flex items-center gap-2 text-xs uppercase tracking-wide text-slate-500">
            <input
              type="checkbox"
              checked={burnSubtitles}
              onChange={(event) => setBurnSubtitles(event.target.checked)}
              className="h-4 w-4 rounded border border-slate-700 bg-slate-900"
            />
            In phụ đề trực tiếp vào video
          </label>

          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3 text-xs text-slate-400">
            <p>
              Hình ảnh sẽ được lặp lại cho tới khi audio kết thúc. Nếu bật “In phụ đề” thì phụ đề sẽ
              được render trực tiếp vào khung hình, ngược lại sẽ được nhúng dạng soft subtitle.
            </p>
            <p className="pt-2 text-[11px] text-slate-500">
              Yêu cầu đã cài đặt `ffmpeg` và `ffprobe` trong PATH.
            </p>
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-3 text-sm text-slate-300">
          <h3 className="text-sm font-semibold uppercase tracking-widest text-slate-400">
            Tuỳ chỉnh phụ đề (burn-in)
          </h3>

          <label className="flex flex-col gap-1">
            <span className="text-xs uppercase tracking-wide text-slate-500">Font</span>
            <select
              value={fontFamily}
              onChange={(event) => setFontFamily(event.target.value)}
              className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
            >
              {FONT_OPTIONS.map((font) => (
                <option key={font} value={font}>
                  {font}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-xs uppercase tracking-wide text-slate-500">Size</span>
            <input
              type="number"
              min={1}
              value={fontSize}
              onChange={(event) => setFontSize(Number(event.target.value) || 1)}
              className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
            />
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-xs uppercase tracking-wide text-slate-500">Màu chữ</span>
            <input
              type="color"
              value={textColor}
              onChange={(event) => setTextColor(event.target.value)}
              className="h-10 w-full rounded border border-slate-700 bg-slate-900"
            />
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-xs uppercase tracking-wide text-slate-500">Màu viền</span>
            <input
              type="color"
              value={outlineColor}
              onChange={(event) => setOutlineColor(event.target.value)}
              className="h-10 w-full rounded border border-slate-700 bg-slate-900"
            />
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-xs uppercase tracking-wide text-slate-500">Độ dày viền</span>
            <input
              type="number"
              min={0}
              step={0.5}
              value={outlineWidth}
              onChange={(event) => setOutlineWidth(Number(event.target.value) || 0)}
              className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
            />
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-xs uppercase tracking-wide text-slate-500">Khoảng cách chữ</span>
            <input
              type="number"
              step={0.5}
              value={letterSpacing}
              onChange={(event) => setLetterSpacing(Number(event.target.value) || 0)}
              className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
            />
          </label>
        </div>

        <div className="flex flex-col gap-3">
          <h3 className="text-sm font-semibold uppercase tracking-widest text-slate-400">
            Preview
          </h3>
          <div className="flex-1 rounded-xl border border-slate-800 bg-black/95 p-6 shadow-[inset_0_0_40px_rgba(0,0,0,0.6)]">
            <div className="flex h-full items-center justify-center">
              <p
                className="font-semibold text-slate-100"
                style={{
                  fontFamily,
                  fontSize,
                  color: textColor,
                  textShadow: buildTextShadow(outlineWidth, outlineColor),
                  letterSpacing: `${letterSpacing}px`,
                  textAlign: "center" as const,
                }}
              >
                {previewText || "Nhập nội dung để xem preview"}
              </p>
            </div>
          </div>
          <input
            value={previewText}
            onChange={(event) => setPreviewText(event.target.value)}
            placeholder="Gõ nội dung phụ đề mẫu..."
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
          />
        </div>
      </div>

      <button
        onClick={handleCompose}
        disabled={busy}
        className="rounded-lg bg-gradient-to-r from-indigo-500 to-emerald-500 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-500/30 transition hover:shadow-indigo-500/40 disabled:cursor-not-allowed disabled:opacity-60"
        type="button"
      >
        {busy ? "Đang render..." : "Ghép & render"}
      </button>

      {status && (
        <p className={`text-sm ${status.tone === "success" ? "text-emerald-300" : "text-rose-300"}`}>
          {status.message}
        </p>
      )}

      {results.length > 0 && (
        <div className="rounded-lg border border-slate-800 bg-slate-900/70 p-3 text-xs text-slate-400">
          <div className="mb-2 font-medium text-slate-200">Xuất thành công ({results.length})</div>
          <ul className="space-y-2 max-h-60 overflow-y-auto pr-2">
            {results.map((item) => (
              <li key={item.output_path} className="space-y-1">
                <div className="flex items-center justify-between text-[11px] uppercase tracking-wide text-slate-500">
                  <span className="truncate" title={item.audio_path}>
                    #{item.index.toString().padStart(3, "0")} · {basename(item.audio_path)}
                  </span>
                  <span className="truncate text-emerald-300" title={item.output_path}>
                    {basename(item.output_path)}
                  </span>
                </div>
                {item.subtitle_path ? (
                  <div className="text-[11px] text-slate-500">
                    Subtitle: {basename(item.subtitle_path)}
                  </div>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

function basename(path: string) {
  const normalised = path.replace(/\\/g, "/");
  const parts = normalised.split("/");
  return parts[parts.length - 1] ?? path;
}

function buildTextShadow(width: number, color: string) {
  if (width <= 0) {
    return "none";
  }
  const offsets = [-width, 0, width];
  const shadows: string[] = [];
  offsets.forEach((x) => {
    offsets.forEach((y) => {
      if (x === 0 && y === 0) return;
      shadows.push(`${x}px ${y}px 0 ${color}`);
    });
  });
  return shadows.join(", ");
}
