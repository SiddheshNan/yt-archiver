import { useState, useEffect, useCallback } from "react";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import IconButton from "@mui/material/IconButton";
import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import LinearProgress from "@mui/material/LinearProgress";
import CircularProgress from "@mui/material/CircularProgress";
import { Icon } from "@iconify/react";
import { videoApi, downloadsApi } from "@/services/api";
import { formatDuration, timeAgo } from "@/utils/format";

const POLL_INTERVAL = 3000;

export default function DownloadQueueModal({ open, onClose }) {
  const [pendingVideos, setPendingVideos] = useState([]);
  const [downloadingVideos, setDownloadingVideos] = useState([]);
  const [queueInfo, setQueueInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchQueue = useCallback(async () => {
    try {
      const [pendingRes, downloadingRes, queueRes] = await Promise.all([
        videoApi.list(1, 50, "pending"),
        videoApi.list(1, 50, "downloading"),
        downloadsApi.queueStatus(),
      ]);
      setPendingVideos(pendingRes.data.items);
      setDownloadingVideos(downloadingRes.data.items);
      setQueueInfo(queueRes.data);
    } catch (err) {
      console.error("Failed to fetch queue:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    fetchQueue();

    const interval = setInterval(fetchQueue, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [open, fetchQueue]);

  const totalInQueue = pendingVideos.length + downloadingVideos.length;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          bgcolor: "#212121",
          color: "#fff",
          borderRadius: 3,
          maxHeight: "80vh",
        },
      }}
    >
      <DialogTitle
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          pb: 1,
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
          <Icon icon="mdi:download-circle-outline" width={26} color="#3EA6FF" />
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Download Queue
          </Typography>
          {totalInQueue > 0 && (
            <Chip
              label={totalInQueue}
              size="small"
              sx={{
                bgcolor: "rgba(62,166,255,0.2)",
                color: "#3EA6FF",
                fontWeight: 700,
                height: 24,
              }}
            />
          )}
        </Box>
        <IconButton onClick={onClose} sx={{ color: "#aaa" }}>
          <Icon icon="mdi:close" width={22} />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ px: 3, pb: 3 }}>
        {/* Queue stats */}
        {queueInfo && (
          <Box
            sx={{
              display: "flex",
              gap: 3,
              mb: 2.5,
              py: 1.5,
              px: 2,
              bgcolor: "rgba(255,255,255,0.05)",
              borderRadius: 2,
            }}
          >
            <StatItem label="In Queue" value={queueInfo.queue_size} />
            <StatItem label="Workers" value={`${queueInfo.active_workers}/${queueInfo.max_workers}`} />
            <StatItem
              label="Status"
              value={queueInfo.running ? "Running" : "Stopped"}
              color={queueInfo.running ? "#22c55e" : "#ff5630"}
            />
          </Box>
        )}

        {loading ? (
          <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
            <CircularProgress size={28} sx={{ color: "#3EA6FF" }} />
          </Box>
        ) : totalInQueue === 0 ? (
          <Box sx={{ textAlign: "center", py: 5 }}>
            <Icon icon="mdi:check-circle-outline" width={48} color="#22c55e" />
            <Typography sx={{ color: "#aaa", mt: 1.5 }}>
              No videos in queue
            </Typography>
            <Typography variant="caption" sx={{ color: "#717171" }}>
              All downloads are complete
            </Typography>
          </Box>
        ) : (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
            {/* Downloading */}
            {downloadingVideos.map((video) => (
              <QueueItem key={video.id} video={video} status="downloading" />
            ))}
            {/* Pending */}
            {pendingVideos.map((video) => (
              <QueueItem key={video.id} video={video} status="pending" onDelete={fetchQueue} />
            ))}
          </Box>
        )}
      </DialogContent>
    </Dialog>
  );
}

function QueueItem({ video, status, onDelete }) {
  const thumbnailUrl = video.thumbnail_path
    ? videoApi.getThumbnailUrl(video.id)
    : video.thumbnail_url;

  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        gap: 1.5,
        p: 1.5,
        borderRadius: 1.5,
        bgcolor: "rgba(255,255,255,0.04)",
        "&:hover": { bgcolor: "rgba(255,255,255,0.07)" },
      }}
    >
      {/* Thumbnail */}
      <Box
        sx={{
          width: 64,
          height: 36,
          borderRadius: 1,
          overflow: "hidden",
          bgcolor: "#181818",
          flexShrink: 0,
          position: "relative",
        }}
      >
        {thumbnailUrl && (
          <Box
            component="img"
            src={thumbnailUrl}
            alt=""
            sx={{ width: "100%", height: "100%", objectFit: "cover" }}
            onError={(e) => { e.target.style.display = "none"; }}
          />
        )}
      </Box>

      {/* Info */}
      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Typography
          variant="body2"
          sx={{
            color: "#f1f1f1",
            fontWeight: 500,
            fontSize: "0.8rem",
            lineHeight: 1.3,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {video.title}
        </Typography>
        <Typography variant="caption" sx={{ color: "#717171" }}>
          {video.channel_name}
        </Typography>
        {status === "downloading" && (
          <LinearProgress
            sx={{
              mt: 0.5,
              height: 3,
              borderRadius: 2,
              bgcolor: "rgba(62,166,255,0.15)",
              "& .MuiLinearProgress-bar": { bgcolor: "#3EA6FF" },
            }}
          />
        )}
      </Box>

      {/* Status badge */}
      <Chip
        icon={
          status === "downloading" ? (
            <Icon icon="mdi:download" width={14} color="#3EA6FF" />
          ) : (
            <Icon icon="mdi:clock-outline" width={14} color="#AAAAAA" />
          )
        }
        label={status === "downloading" ? "Downloading" : "Pending"}
        size="small"
        sx={{
          bgcolor: status === "downloading" ? "rgba(62,166,255,0.15)" : "rgba(255,255,255,0.08)",
          color: status === "downloading" ? "#3EA6FF" : "#AAAAAA",
          fontSize: 11,
          height: 24,
          flexShrink: 0,
        }}
      />
      
      {/* Delete from Queue Button */}
      {status === "pending" && (
        <IconButton 
          size="small" 
          sx={{ color: "#ff4444", "&:hover": { bgcolor: "rgba(255,68,68,0.1)" } }}
          onClick={async (e) => {
            e.stopPropagation();
            if (!window.confirm("Remove this pending video from the download queue?")) return;
            try {
              await videoApi.delete(video.id);
              if (onDelete) onDelete();
            } catch (err) {
              console.error("Failed to remove pending video from queue", err);
            }
          }}
        >
          <Icon icon="mdi:trash-can-outline" width={18} />
        </IconButton>
      )}
    </Box>
  );
}

function StatItem({ label, value, color = "#f1f1f1" }) {
  return (
    <Box sx={{ textAlign: "center" }}>
      <Typography variant="body2" sx={{ color, fontWeight: 700, fontSize: "1rem" }}>
        {value}
      </Typography>
      <Typography variant="caption" sx={{ color: "#717171" }}>
        {label}
      </Typography>
    </Box>
  );
}
