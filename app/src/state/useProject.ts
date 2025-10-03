import { create } from "zustand";
import type { Project, Scene } from "../types/project";

const emptyProject: Project = {
  metadata: {
    title: "Demo project"
  },
  output: {
    resolution: { width: 1920, height: 1080 },
    frame_rate: 30,
    format: "H264"
  },
  scenes: [
    {
      id: "scene-1",
      duration_secs: 5,
      media: { type: "Image", path: "assets/scene-1.jpg" }
    }
  ],
  subtitle_style: {
    font_family: "Arial",
    font_size: 48,
    color: { r: 1, g: 1, b: 1, a: 1 },
    alignment: "Bottom"
  }
};

type ProjectState = {
  project: Project;
  setProject: (project: Project) => void;
  updateScene: (scene: Scene) => void;
};

export const useProject = create<ProjectState>((set) => ({
  project: emptyProject,
  setProject: (project) => set({ project }),
  updateScene: (scene) =>
    set((state) => ({
      project: {
        ...state.project,
        scenes: state.project.scenes.map((item) => (item.id === scene.id ? scene : item))
      }
    }))
}));
