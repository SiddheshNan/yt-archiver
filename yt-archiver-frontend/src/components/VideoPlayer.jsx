import { useRef, useEffect, useState } from "react";
import Plyr from "plyr";
import "plyr/dist/plyr.css";
import Box from "@mui/material/Box";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import { Icon } from "@iconify/react";
import StatsForNerdsOverlay from "./StatsForNerdsOverlay";

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
export default function VideoPlayer({ src, poster, videoId }) {
  const containerRef = useRef(null);
  const playerRef = useRef(null);
  const [videoEl, setVideoEl] = useState(null);
  const [contextMenu, setContextMenu] = useState(null);
  const [showStats, setShowStats] = useState(false);

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
    setVideoEl(video);

    return () => {
      if (playerRef.current) {
        playerRef.current.destroy();
        playerRef.current = null;
      }
    };
  }, [src, poster]);

  const handleContextMenu = (event) => {
    event.preventDefault();
    setContextMenu(
      contextMenu === null
        ? { mouseX: event.clientX, mouseY: event.clientY }
        : null
    );
  };

  const handleCloseContext = () => {
    setContextMenu(null);
  };

  const handleToggleStats = () => {
    setShowStats(!showStats);
    handleCloseContext();
  };

  return (
    <Box
      onContextMenu={handleContextMenu}
      sx={{
        position: "relative",
        width: "100%",
        // aspectRatio: "16 / 9", // we dont want this as videos can be of any aspect ratio
        maxHeight: "80vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        bgcolor: "#000",
        borderRadius: { xs: 0, lg: "12px" },
        overflow: "hidden",
        "& .plyr-container": {
          width: "100%",
          height: "100%",
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
            width: "100%",
            height: "100%",
          },
          "& .plyr__control--overlaid": {
            bgcolor: "rgba(0,110,255,0.85)",
            "&:hover": { bgcolor: "#006effff" },
          },
          "& .plyr--fullscreen-active": {
            borderRadius: "0 !important"
          }
        }
      }}
    >
      <Box className="plyr-container" ref={containerRef} />

      {showStats && (
        <StatsForNerdsOverlay
          videoElement={videoEl}
          onClose={() => setShowStats(false)}
          videoId={videoId}
        />
      )}

      <Menu
        open={contextMenu !== null}
        onClose={handleCloseContext}
        anchorReference="anchorPosition"
        anchorPosition={
          contextMenu !== null
            ? { top: contextMenu.mouseY, left: contextMenu.mouseX }
            : undefined
        }
        PaperProps={{
          sx: { bgcolor: "#272727", color: "#fff", borderRadius: 2 },
        }}
        MenuListProps={{
          sx: { py: 0.5 }
        }}
      >
        <MenuItem onClick={handleToggleStats} sx={{ fontSize: "0.85rem", minHeight: "auto", px: 2, "&:hover": { bgcolor: "rgba(255,255,255,0.1)" } }}>
          <ListItemIcon sx={{ color: "#fff", minWidth: 28 }}>
            <Icon icon="mdi:chart-box-outline" width={18} />
          </ListItemIcon>
          <ListItemText primary="Stats for nerds" primaryTypographyProps={{ fontSize: "0.85rem", fontWeight: 500 }} />
        </MenuItem>
      </Menu>
    </Box>
  );
}
