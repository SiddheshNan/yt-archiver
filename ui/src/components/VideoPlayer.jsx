import { useRef, useEffect, useState } from "react";
import Plyr from "plyr";
import "plyr/dist/plyr.css";
import Box from "@mui/material/Box";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import Divider from "@mui/material/Divider";
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
    "captions",
    "settings",
    "pip",
    "airplay",
    "fullscreen",
  ],
  settings: ["captions", "speed"],
  speed: { selected: 1, options: [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2] },
  keyboard: { focused: true, global: true },
  tooltips: { controls: true, seek: true },
  seekTime: 5,
  autoplay: true,
  captions: { active: false, update: true },
};

/**
 * Plyr video player component.
 *
 * Uses the vanilla Plyr library directly (not plyr-react) for maximum
 * control and to avoid React 18 strict-mode double-mount issues.
 */
export default function VideoPlayer({ src, poster, videoId, ytaId, subtitleTracks = [] }) {
  const containerRef = useRef(null);
  const playerRef = useRef(null);
  const [videoEl, setVideoEl] = useState(null);
  const [contextMenu, setContextMenu] = useState(null);
  const [showStats, setShowStats] = useState(false);
  const [isLooping, setIsLooping] = useState(false);

  useEffect(() => {
    if (!containerRef.current || !src) return;

    // Create video element
    const video = document.createElement("video");
    video.setAttribute("playsinline", "");
    video.setAttribute("controls", "");
    video.setAttribute("crossorigin", "anonymous");
    if (poster) video.setAttribute("poster", poster);

    const source = document.createElement("source");
    source.setAttribute("src", src);
    source.setAttribute("type", "video/mp4");
    video.appendChild(source);

    // Add subtitle tracks
    subtitleTracks.forEach((track, idx) => {
      const trackEl = document.createElement("track");
      trackEl.setAttribute("kind", "captions");
      trackEl.setAttribute("src", track.src);
      trackEl.setAttribute("srclang", track.lang.split("-")[0]);
      trackEl.setAttribute("label", track.label);
      video.appendChild(trackEl);
    });

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
  }, [src, poster, subtitleTracks]);

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

  const handleToggleLoop = () => {
    const next = !isLooping;
    setIsLooping(next);
    if (videoEl) videoEl.loop = next;
    handleCloseContext();
  };

  const handleCopyYoutubeUrl = () => {
    const ytUrl = `https://www.youtube.com/watch?v=${videoId}`;
    navigator.clipboard.writeText(ytUrl);
    handleCloseContext();
  };

  const handleCopyArchiveUrl = () => {
    navigator.clipboard.writeText(window.location.href);
    handleCloseContext();
  };

  const menuItemSx = { fontSize: "0.85rem", minHeight: "auto", px: 2, "&:hover": { bgcolor: "rgba(255,255,255,0.1)" } };

  return (
    <Box
      onContextMenu={handleContextMenu}
      sx={{
        position: "relative",
        width: "100%",
        maxHeight: "80vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        bgcolor: "#000",
        borderRadius: { xs: 0, lg: "12px" },
        overflow: "hidden",
        "& .plyr-container": {
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
            width: "100%",
            "&.plyr--fullscreen-active, &:fullscreen, &:-webkit-full-screen": {
              borderRadius: "0 !important",
              maxHeight: "none !important",
              height: "100dvh !important",
              "& .plyr__video-wrapper": {
                maxHeight: "none !important",
                height: "100dvh !important",
              },
              "& video": {
                maxHeight: "none !important",
                height: "100dvh !important",
              },
            },
          },
          "& .plyr__video-wrapper": {
            maxHeight: "80vh",
            bgcolor: "#000",
          },
          "& video": {
            maxHeight: "80vh",
            objectFit: "contain",
          },
          "& .plyr__control--overlaid": {
            bgcolor: "rgba(0,110,255,0.85)",
            "&:hover": { bgcolor: "#006effff" },
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
          ytaId={ytaId}
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
          sx: { bgcolor: "#272727", color: "#fff", borderRadius: 2, minWidth: 200 },
        }}
        MenuListProps={{
          sx: { py: 0.5 }
        }}
      >
        <MenuItem onClick={handleToggleLoop} sx={menuItemSx}>
          <ListItemIcon sx={{ color: "#fff", minWidth: 28 }}>
            <Icon icon={isLooping ? "mdi:check" : "mdi:repeat"} width={18} />
          </ListItemIcon>
          <ListItemText primary={isLooping ? "Loop: On" : "Loop"} primaryTypographyProps={{ fontSize: "0.85rem", fontWeight: 500 }} />
        </MenuItem>
        <Divider sx={{ borderColor: "rgba(255,255,255,0.1)", my: 0.5 }} />
        <MenuItem onClick={handleCopyYoutubeUrl} sx={menuItemSx}>
          <ListItemIcon sx={{ color: "#fff", minWidth: 28 }}>
            <Icon icon="mdi:youtube" width={18} />
          </ListItemIcon>
          <ListItemText primary="Copy YouTube URL" primaryTypographyProps={{ fontSize: "0.85rem", fontWeight: 500 }} />
        </MenuItem>
        <MenuItem onClick={handleCopyArchiveUrl} sx={menuItemSx}>
          <ListItemIcon sx={{ color: "#fff", minWidth: 28 }}>
            <Icon icon="mdi:link-variant" width={18} />
          </ListItemIcon>
          <ListItemText primary="Copy archive URL" primaryTypographyProps={{ fontSize: "0.85rem", fontWeight: 500 }} />
        </MenuItem>
        <Divider sx={{ borderColor: "rgba(255,255,255,0.1)", my: 0.5 }} />
        <MenuItem onClick={handleToggleStats} sx={menuItemSx}>
          <ListItemIcon sx={{ color: "#fff", minWidth: 28 }}>
            <Icon icon="mdi:chart-box-outline" width={18} />
          </ListItemIcon>
          <ListItemText primary="Stats for nerds" primaryTypographyProps={{ fontSize: "0.85rem", fontWeight: 500 }} />
        </MenuItem>
      </Menu>
    </Box>
  );
}
