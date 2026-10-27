import { useState, useEffect } from "react";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import IconButton from "@mui/material/IconButton";
import { Icon } from "@iconify/react";

export default function StatsForNerdsOverlay({ videoElement, onClose, videoId, ytaId }) {
  const [stats, setStats] = useState({
    videoId: videoId || "unavailable",
    ytaId: ytaId || "unavailable",
    viewport: "0x0",
    resolution: "0x0",
    volume: "100%",
    codecs: "avc1 / mp4a",
    connectionSpeed: "0 Kbps",
    networkActivity: "0 KB",
    bufferHealth: "0.00 s",
    droppedFrames: "0 / 0",
  });

  useEffect(() => {
    if (!videoElement) return;

    const updateStats = () => {
      const p = videoElement;
      
      const viewport = `${p.clientWidth}x${p.clientHeight}`;
      const resolution = `${p.videoWidth}x${p.videoHeight}`;
      
      const volume = `${Math.round(p.volume * 100)}%`;
      
      let bufferHealth = "0.00 s";
      if (p.buffered.length > 0) {
        const bufferedEnd = p.buffered.end(p.buffered.length - 1);
        const health = Math.max(0, bufferedEnd - p.currentTime);
        bufferHealth = `${health.toFixed(2)} s`;
      }
      
      let droppedFrames = "0 / 0";
      if (p.getVideoPlaybackQuality) {
        const quality = p.getVideoPlaybackQuality();
        droppedFrames = `${quality.droppedVideoFrames} / ${quality.totalVideoFrames}`;
      }
      
      setStats((prev) => ({
        ...prev,
        viewport,
        resolution,
        volume,
        bufferHealth,
        droppedFrames,
      }));
    };

    updateStats();
    const intervalId = setInterval(updateStats, 500);
    
    return () => clearInterval(intervalId);
  }, [videoElement]);

  return (
    <Box
      sx={{
        position: "absolute",
        top: 16,
        left: 16,
        bgcolor: "rgba(0, 0, 0, 0.65)",
        backdropFilter: "blur(4px)",
        color: "#fff",
        p: 2,
        borderRadius: 1,
        fontFamily: "'Roboto Mono', monospace",
        fontSize: "0.75rem",
        zIndex: 9999,
        width: 382,
        pointerEvents: "auto",
        boxShadow: "0 4px 6px rgba(0,0,0,0.3)",
      }}
      onClick={(e) => e.stopPropagation()}
      onContextMenu={(e) => e.stopPropagation()}
      onDoubleClick={(e) => e.stopPropagation()}
    >
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1, borderBottom: "1px solid rgba(255,255,255,0.2)", pb: 0.5 }}>
        <Typography variant="caption" sx={{ fontWeight: "bold", fontFamily: "inherit" }}>
          Stats for nerds
        </Typography>
        <IconButton size="small" onClick={onClose} sx={{ color: "#aaa", p: 0.25, "&:hover": { color: "#fff" } }}>
          <Icon icon="mdi:close" width={16} />
        </IconButton>
      </Box>
      
      <StatRow label="YT ID" value={stats.videoId} />
      <StatRow label="YTA ID" value={stats.ytaId} />
      <StatRow label="Viewport / Frames" value={`${stats.viewport} / ${stats.droppedFrames} dropped`} />
      <StatRow label="Current / Optimal Res" value={`${stats.resolution} / ${stats.resolution}`} />
      <StatRow label="Volume / Normalized" value={`${stats.volume} / ${stats.volume}`} />
      <StatRow label="Codecs" value={stats.codecs} />
      {/* <StatRow label="Connection Speed" value="0 Kbps (Native)" />
      <StatRow label="Network Activity" value="0 KB (Native)" /> */}
      <StatRow label="Buffer Health" value={stats.bufferHealth} />
    </Box>
  );
}

function StatRow({ label, value }) {
  return (
    <Box sx={{ display: "flex", mb: 0.75, lineHeight: 1.2 }}>
      <Box sx={{ width: 145, color: "#ccc", flexShrink: 0 }}>{label}</Box>
      <Box sx={{ flex: 1, wordBreak: "break-all" }}>{value}</Box>
    </Box>
  );
}
