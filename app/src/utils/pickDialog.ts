import { invoke } from "@tauri-apps/api/core";

export type PickDialogKind = "directory" | "file" | "save";

export type PickDialogOptions = {
  kind: PickDialogKind;
  title?: string;
  defaultPath?: string;
  fileName?: string;
  filters?: { name: string; extensions: string[] }[];
};

export type PickResult = {
  path: string;
  cancelled: boolean;
};

export async function pickPath(options: PickDialogOptions): Promise<PickResult> {
  try {
    const result = await invoke<string | null>("command_pick_path", { options });
    if (!result) {
      return { path: "", cancelled: true };
    }
    return { path: result, cancelled: false };
  } catch (error) {
    console.error("Failed to open picker", error);
    return { path: "", cancelled: false };
  }
}
