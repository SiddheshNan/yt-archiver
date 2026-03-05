import { useRef, useEffect } from "react";
import Plyr from "plyr";
import "plyr/dist/plyr.css";
import Box from "@mui/material/Box";

const PLYR_OPTIONS = {
  controls: [
    "play-large",
    // "rewind",
    "play",
    // "fast-forward",
    "progress",
    "current-time",
    "duration",
    "mute",
    "volume",
    "settings",
    "pip",
    "airplay",
    "fullscreen",
  ],
  settings: ["speed"],
  speed: { selected: 1, options: [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2] },
  keyboard: { focused: true, global: true },
  tooltips: { controls: true, seek: true },
  seekTime: 5,
  autoplay: true,
};

/**
 * Plyr video player component.
 *
 * Uses the vanilla Plyr library directly (not plyr-react) for maximum
 * control and to avoid React 18 strict-mode double-mount issues.
 */
export default function VideoPlayer({ src, poster }) {
  const containerRef = useRef(null);
  const playerRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current || !src) return;

    // Create video element
    const video = document.createElement("video");
    video.setAttribute("playsinline", "");
    video.setAttribute("controls", "");
    if (poster) video.setAttribute("poster", poster);

    const source = document.createElement("source");
    source.setAttribute("src", src);
    source.setAttribute("type", "video/mp4");
    video.appendChild(source);

    // Clear container and append
    containerRef.current.innerHTML = "";
    containerRef.current.appendChild(video);

    // Initialize Plyr
    playerRef.current = new Plyr(video, PLYR_OPTIONS);

    return () => {
      if (playerRef.current) {
        playerRef.current.destroy();
        playerRef.current = null;
      }
    };
  }, [src, poster]);

  return (
    <Box
      ref={containerRef}
      sx={{
        width: "100%",
        "--plyr-color-main": "#006effff",
        "--plyr-video-background": "#000",
        "--plyr-menu-background": "#272727",
        "--plyr-menu-color": "#fff",
        "--plyr-menu-border-color": "rgba(255,255,255,0.1)",
        "--plyr-badge-background": "#006effff",
        "--plyr-badge-text-color": "#fff",
        "--plyr-tooltip-background": "#272727",
        "--plyr-tooltip-color": "#fff",
        "--plyr-font-family": "'DM Sans Variable', sans-serif",
        "& .plyr": {
          borderRadius: { xs: 0, lg: "12px" },
          overflow: "hidden",
        },
        "& .plyr__control--overlaid": {
          bgcolor: "rgba(0,110,255,0.85)",
          "&:hover": { bgcolor: "#006effff" },
        },
      }}
    />
  );
}
