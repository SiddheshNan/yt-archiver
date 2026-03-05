import { useState } from "react";
import { Helmet } from "react-helmet-async";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import Alert from "@mui/material/Alert";
import CircularProgress from "@mui/material/CircularProgress";
import Divider from "@mui/material/Divider";
import Badge from "@mui/material/Badge";
import { Icon } from "@iconify/react";
import { videoApi, channelApi } from "@/services/api";
import DownloadQueueModal from "@/components/DownloadQueueModal";

export default function AddVideoPage() {
  // Single video
  const [videoUrl, setVideoUrl] = useState("");
  const [videoLoading, setVideoLoading] = useState(false);
  const [videoResult, setVideoResult] = useState(null);
  const [videoError, setVideoError] = useState("");

  // Channel
  const [channelUrl, setChannelUrl] = useState("");
  const [channelLoading, setChannelLoading] = useState(false);
  const [channelResult, setChannelResult] = useState(null);
  const [channelError, setChannelError] = useState("");

  // Playlist
  const [playlistUrl, setPlaylistUrl] = useState("");
  const [playlistLoading, setPlaylistLoading] = useState(false);
  const [playlistResult, setPlaylistResult] = useState(null);
  const [playlistError, setPlaylistError] = useState("");

  // Queue modal
  const [queueOpen, setQueueOpen] = useState(false);

  const handleAddVideo = async (e) => {
    e.preventDefault();
    if (!videoUrl.trim()) return;
    setVideoLoading(true);
    setVideoError("");
    setVideoResult(null);
    try {
      const { data } = await videoApi.add(videoUrl.trim());
      setVideoResult(data);
      setVideoUrl("");
    } catch (err) {
      const msg = err.response?.data?.error?.message || err.response?.data?.detail || err.message;
      setVideoError(msg);
    } finally {
      setVideoLoading(false);
    }
  };

  const handleArchiveChannel = async (e) => {
    e.preventDefault();
    if (!channelUrl.trim()) return;
    setChannelLoading(true);
    setChannelError("");
    setChannelResult(null);
    try {
      const { data } = await channelApi.archive(channelUrl.trim());
      setChannelResult(data);
      setChannelUrl("");
    } catch (err) {
      const msg = err.response?.data?.error?.message || err.response?.data?.detail || err.message;
      setChannelError(msg);
    } finally {
      setChannelLoading(false);
    }
  };

  const handleDownloadPlaylist = async (e) => {
    e.preventDefault();
    if (!playlistUrl.trim()) return;
    setPlaylistLoading(true);
    setPlaylistError("");
    setPlaylistResult(null);
    try {
      const { data } = await videoApi.addPlaylist(playlistUrl.trim());
      setPlaylistResult(data);
      setPlaylistUrl("");
    } catch (err) {
      const msg = err.response?.data?.error?.message || err.response?.data?.detail || err.message;
      setPlaylistError(msg);
    } finally {
      setPlaylistLoading(false);
    }
  };

  const inputSx = {
    "& .MuiOutlinedInput-root": {
      bgcolor: "#121212",
      color: "#fff",
      "& fieldset": { borderColor: "rgba(255,255,255,0.2)" },
      "&:hover fieldset": { borderColor: "rgba(255,255,255,0.4)" },
      "&.Mui-focused fieldset": { borderColor: "#3EA6FF" },
    },
    "& .MuiInputLabel-root": { color: "#717171" },
    "& .MuiInputLabel-root.Mui-focused": { color: "#3EA6FF" },
  };

  return (
    <Box sx={{ maxWidth: 700, mx: "auto", px: 3, py: 5 }}>
      <Helmet>
        <title>Add Videos - YouTube Archiver</title>
        <meta name="description" content="Add YouTube videos, channels, or playlists to your archive" />
      </Helmet>
      {/* Header with queue button */}
      <Box sx={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", mb: 5 }}>
        <Box>
          <Typography variant="h4" sx={{ color: "#fff", fontWeight: 700, mb: 1 }}>
            Add Videos
          </Typography>
          <Typography variant="body2" sx={{ color: "#AAAAAA" }}>
            Paste a YouTube video or channel URL to queue for download
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<Icon icon="mdi:download-circle-outline" width={20} />}
          onClick={() => setQueueOpen(true)}
          sx={{
            color: "#3EA6FF",
            borderColor: "rgba(62,166,255,0.4)",
            borderRadius: 3,
            textTransform: "none",
            fontWeight: 600,
            px: 2.5,
            flexShrink: 0,
            "&:hover": { borderColor: "#3EA6FF", bgcolor: "rgba(62,166,255,0.1)" },
          }}
        >
          View Queue
        </Button>
      </Box>

      {/* ── Single Video ── */}
      <Box sx={{ mb: 5 }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 2.5 }}>
          <Icon icon="mdi:play-circle-outline" width={28} color="#FF0000" />
          <Typography variant="h6" sx={{ color: "#f1f1f1", fontWeight: 600 }}>
            Add Single Video
          </Typography>
        </Box>

        <Box component="form" onSubmit={handleAddVideo} sx={{ display: "flex", gap: 1.5 }}>
          <TextField
            fullWidth
            size="small"
            label="YouTube Video URL"
            placeholder="https://www.youtube.com/watch?v=..."
            value={videoUrl}
            onChange={(e) => setVideoUrl(e.target.value)}
            disabled={videoLoading}
            sx={inputSx}
          />
          <Button
            type="submit"
            variant="contained"
            disabled={videoLoading || !videoUrl.trim()}
            sx={{
              bgcolor: "#FF0000",
              minWidth: 120,
              fontWeight: 600,
              "&:hover": { bgcolor: "#CC0000" },
              "&.Mui-disabled": { bgcolor: "rgba(255,0,0,0.3)", color: "rgba(255,255,255,0.5)" },
            }}
          >
            {videoLoading ? <CircularProgress size={20} sx={{ color: "#fff" }} /> : "Download"}
          </Button>
        </Box>

        {videoLoading && (
          <Typography variant="caption" sx={{ color: "#717171", mt: 1.5, display: "block" }}>
            Extracting video metadata... this takes a few seconds
          </Typography>
        )}

        {videoError && (
          <Alert severity="error" sx={{ mt: 2, bgcolor: "rgba(255,86,48,0.12)", color: "#ff5630" }}>
            {videoError}
          </Alert>
        )}
        {videoResult && (
          <Alert
            severity="success"
            icon={<Icon icon="mdi:check-circle" width={22} color="#22c55e" />}
            sx={{ mt: 2, bgcolor: "rgba(34,197,94,0.12)", color: "#22c55e" }}
          >
            <strong>Added to queue!</strong> Video "{videoResult.video_id}" is queued for download.
            <Box
              component="span"
              sx={{ ml: 1, cursor: "pointer", textDecoration: "underline", "&:hover": { color: "#4ade80" } }}
              onClick={() => setQueueOpen(true)}
            >
              View queue →
            </Box>
          </Alert>
        )}
      </Box>

      <Divider sx={{ borderColor: "rgba(255,255,255,0.1)", my: 4 }} />

      {/* ── Channel Archive ── */}
      <Box>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 2.5 }}>
          <Icon icon="mdi:account-circle-outline" width={28} color="#3EA6FF" />
          <Typography variant="h6" sx={{ color: "#f1f1f1", fontWeight: 600 }}>
            Archive Entire Channel
          </Typography>
        </Box>

        <Box component="form" onSubmit={handleArchiveChannel} sx={{ display: "flex", gap: 1.5 }}>
          <TextField
            fullWidth
            size="small"
            label="YouTube Channel URL"
            placeholder="https://www.youtube.com/@channelname"
            value={channelUrl}
            onChange={(e) => setChannelUrl(e.target.value)}
            disabled={channelLoading}
            sx={inputSx}
          />
          <Button
            type="submit"
            variant="contained"
            disabled={channelLoading || !channelUrl.trim()}
            sx={{
              bgcolor: "#3EA6FF",
              color: "#0f0f0f",
              minWidth: 120,
              fontWeight: 600,
              "&:hover": { bgcolor: "#65b8ff" },
              "&.Mui-disabled": { bgcolor: "rgba(62,166,255,0.3)", color: "rgba(255,255,255,0.5)" },
            }}
          >
            {channelLoading ? <CircularProgress size={20} sx={{ color: "#fff" }} /> : "Archive"}
          </Button>
        </Box>

        {channelLoading && (
          <Typography variant="caption" sx={{ color: "#717171", mt: 1.5, display: "block" }}>
            Extracting channel videos... this may take a while for large channels
          </Typography>
        )}

        {channelError && (
          <Alert severity="error" sx={{ mt: 2, bgcolor: "rgba(255,86,48,0.12)", color: "#ff5630" }}>
            {channelError}
          </Alert>
        )}
        {channelResult && (
          <Alert
            severity="success"
            icon={<Icon icon="mdi:check-circle" width={22} color="#22c55e" />}
            sx={{ mt: 2, bgcolor: "rgba(34,197,94,0.12)", color: "#22c55e" }}
          >
            <strong>{channelResult.queued?.length || 0} video(s) added to queue!</strong>
            {channelResult.errors?.length > 0 && (
              <span> ({channelResult.errors.length} skipped/already archived)</span>
            )}
            <Box
              component="span"
              sx={{ ml: 1, cursor: "pointer", textDecoration: "underline", "&:hover": { color: "#4ade80" } }}
              onClick={() => setQueueOpen(true)}
            >
              View queue →
            </Box>
          </Alert>
        )}

        <Typography variant="caption" sx={{ color: "#717171", display: "block", mt: 2 }}>
          This will extract all videos from the channel and queue them for download.
          Already-archived videos will be skipped.
        </Typography>
      </Box>

      <Divider sx={{ borderColor: "rgba(255,255,255,0.1)", my: 4 }} />

      {/* ── Playlist Download ── */}
      <Box mb={4}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 2.5 }}>
          <Icon icon="mdi:playlist-play" width={32} color="#4ade80" />
          <Typography variant="h6" sx={{ color: "#f1f1f1", fontWeight: 600 }}>
            Download Entire Playlist
          </Typography>
        </Box>

        <Box component="form" onSubmit={handleDownloadPlaylist} sx={{ display: "flex", gap: 1.5 }}>
          <TextField
            fullWidth
            size="small"
            label="YouTube Playlist URL"
            placeholder="https://www.youtube.com/playlist?list=..."
            value={playlistUrl}
            onChange={(e) => setPlaylistUrl(e.target.value)}
            disabled={playlistLoading}
            sx={inputSx}
          />
          <Button
            type="submit"
            variant="contained"
            disabled={playlistLoading || !playlistUrl.trim()}
            sx={{
              bgcolor: "#22c55e",
              color: "#fff",
              minWidth: 130,
              fontWeight: 600,
              "&:hover": { bgcolor: "#16a34a" },
              "&.Mui-disabled": { bgcolor: "rgba(34,197,94,0.3)", color: "rgba(255,255,255,0.5)" },
            }}
          >
            {playlistLoading ? <CircularProgress size={20} sx={{ color: "#fff" }} /> : "Download"}
          </Button>
        </Box>

        {playlistLoading && (
          <Typography variant="caption" sx={{ color: "#717171", mt: 1.5, display: "block" }}>
            Extracting playlist videos... this may take a while for large playlists
          </Typography>
        )}

        {playlistError && (
          <Alert severity="error" sx={{ mt: 2, bgcolor: "rgba(255,86,48,0.12)", color: "#ff5630" }}>
            {playlistError}
          </Alert>
        )}
        {playlistResult && (
          <Alert
            severity="success"
            icon={<Icon icon="mdi:check-circle" width={22} color="#22c55e" />}
            sx={{ mt: 2, bgcolor: "rgba(34,197,94,0.12)", color: "#22c55e" }}
          >
            <strong>{playlistResult.queued?.length || 0} video(s) added from playlist to queue!</strong>
            {playlistResult.errors?.length > 0 && (
              <span> ({playlistResult.errors.length} skipped/already archived)</span>
            )}
            <Box
              component="span"
              sx={{ ml: 1, cursor: "pointer", textDecoration: "underline", "&:hover": { color: "#4ade80" } }}
              onClick={() => setQueueOpen(true)}
            >
              View queue →
            </Box>
          </Alert>
        )}
      </Box>

      {/* Queue modal */}
      <DownloadQueueModal open={queueOpen} onClose={() => setQueueOpen(false)} />
    </Box>
  );
}
