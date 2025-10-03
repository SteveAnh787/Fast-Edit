export type Color = {
  r: number;
  g: number;
  b: number;
  a: number;
};

export type SubtitleStyle = {
  font_family: string;
  font_size: number;
  color: Color;
  alignment: "Bottom" | "Middle" | "Top";
};

export type MediaAsset =
  | { type: "Image"; path: string }
  | { type: "Video"; path: string };

export type Scene = {
  id: string;
  duration_secs: number;
  media: MediaAsset;
};

export type Project = {
  metadata: {
    title: string;
  };
  output: {
    resolution: {
      width: number;
      height: number;
    };
    frame_rate: number;
    format: "H264" | "H265" | "ProRes";
  };
  scenes: Scene[];
  subtitle_style: SubtitleStyle;
};
