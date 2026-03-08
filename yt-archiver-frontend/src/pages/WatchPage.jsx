import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import CircularProgress from "@mui/material/CircularProgress";
import ThumbUpOutlinedIcon from "@mui/icons-material/ThumbUpOutlined";
import ThumbDownOutlinedIcon from "@mui/icons-material/ThumbDownOutlined";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import DeleteOutlinedIcon from "@mui/icons-material/DeleteOutlined";
import { Icon } from "@iconify/react";
import VideoPlayer from "@/components/VideoPlayer";
import ChannelAvatar from "@/components/ChannelAvatar";
import Alert from "@mui/material/Alert";
import { videoApi, channelApi } from "@/services/api";
import { formatDuration, timeAgo, formatFileSize, formatViews } from "@/utils/format";

export default function WatchPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [video, setVideo] = useState(null);
  const [channel, setChannel] = useState(null);
  const [relatedVideos, setRelatedVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showFullDescription, setShowFullDescription] = useState(false);
  
  // Rearchive State
  const [rearchiving, setRearchiving] = useState(false);
  const [rearchiveMessage, setRearchiveMessage] = useState(null);
  const [rearchiveError, setRearchiveError] = useState(null);

  useEffect(() => {
    const fetchVideo = async () => {
      try {
        setLoading(true);
        const { data } = await videoApi.get(id);
        setVideo(data);

        // Fetch related videos (blends same-channel and text search)
        const { data: related } = await videoApi.getRelatedVideos(id, 20);
        setRelatedVideos(related);

        // Fetch channel info for video count
        if (data.channel_id) {
          channelApi.get(data.channel_id)
            .then(({ data: ch }) => setChannel(ch))
            .catch(() => {});
        }
      } catch (err) {
        console.error("Failed to fetch video:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchVideo();
    window.scrollTo(0, 0);
  }, [id]);

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 10 }}>
        <CircularProgress sx={{ color: "#fff" }} />
      </Box>
    );
  }

  if (!video) {
    return (
      <Box sx={{ textAlign: "center", py: 10 }}>
        <Typography variant="h5" sx={{ color: "#aaa" }}>Video not found</Typography>
      </Box>
    );
  }

  const streamUrl = videoApi.getStreamUrl(id);
  const posterUrl = video.thumbnail_path
    ? videoApi.getThumbnailUrl(id)
    : video.thumbnail_url;

  // Build subtitle track list for the player
  const subtitleTracks = (video.subtitle_tracks || []).map((t) => ({
    lang: t.lang,
    label: t.label,
    src: videoApi.getSubtitleUrl(id, t.lang),
  }));

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: { xs: "column", lg: "row" },
        gap: 3,
        px: { xs: 0, lg: 3 },
        py: { xs: 0, lg: 3 },
        maxWidth: 1800,
        mx: "auto",
      }}
    >
      <Helmet>
        <title>{video.title} - YouTube Archiver</title>
        <meta name="description" content={video.description ? video.description.slice(0, 160) : video.title} />
      </Helmet>
      {/* ── Main Column ── */}
      <Box sx={{ flex: 1, minWidth: 0 }}>
        {/* Video Player */}
        {video.status === "completed" ? (
          <VideoPlayer src={streamUrl} poster={posterUrl} videoId={video.video_id || video.id} subtitleTracks={subtitleTracks} />
        ) : (
          <Box
            sx={{
              position: "relative",
              width: "100%",
              paddingTop: "56.25%",
              bgcolor: "#000",
              borderRadius: { xs: 0, lg: 2 },
              overflow: "hidden",
            }}
          >
            <Box
              sx={{
                position: "absolute",
                top: 0, left: 0, width: "100%", height: "100%",
                display: "flex", alignItems: "center", justifyContent: "center",
                flexDirection: "column", gap: 2,
              }}
            >
              {video.status === "downloading" ? (
                <>
                  <CircularProgress sx={{ color: "#3EA6FF" }} />
                  <Typography sx={{ color: "#aaa" }}>Downloading...</Typography>
                </>
              ) : video.status === "pending" ? (
                <>
                  <Icon icon="mdi:clock-outline" width={48} color="#888" />
                  <Typography sx={{ color: "#aaa" }}>Pending download</Typography>
                </>
              ) : (
                <>
                  <Icon icon="mdi:alert-circle-outline" width={48} color="#ff4444" />
                  <Typography sx={{ color: "#ff4444" }}>Download failed</Typography>
                  {video.error_message && (
                    <Typography variant="caption" sx={{ color: "#888", maxWidth: 400, textAlign: "center" }}>
                      {video.error_message}
                    </Typography>
                  )}
                </>
              )}
            </Box>
          </Box>
        )}
        
        {rearchiveMessage && (
          <Alert severity="success" sx={{ mt: 2, bgcolor: "rgba(34,197,94,0.1)", color: "#4ade80" }}>
            {rearchiveMessage}
          </Alert>
        )}
        {rearchiveError && (
          <Alert severity="error" sx={{ mt: 2, bgcolor: "rgba(255,86,48,0.1)", color: "#ff5630" }}>
            {rearchiveError}
          </Alert>
        )}

        {/* ── Video Info (YouTube-style) ── */}
        <Box sx={{ px: { xs: 2, lg: 0 }, mt: 1.5 }}>
          {/* Title */}
          <Typography
            variant="h6"
            sx={{
              color: "#fff",
              fontWeight: 700,
              lineHeight: 1.3,
              fontSize: { xs: "1.1rem", sm: "1.25rem" },
              mb: 1.5,
            }}
          >
            {video.title}
          </Typography>

          {/* Actions Row */}
          <Box
            sx={{
              display: "flex",
              alignItems: { xs: "flex-start", sm: "center" },
              justifyContent: "space-between",
              flexDirection: { xs: "column", sm: "row" },
              gap: 2,
              mb: 2,
            }}
          >
            {/* Channel Info */}
            <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
              <ChannelAvatar
                channelId={video.channel_id}
                channelName={video.channel_name}
                size={40}
                onClick={() => video.channel_id && navigate(`/channel/${video.channel_id}`)}
              />
              <Box>
                <Typography
                  variant="subtitle2"
                  sx={{
                    color: "#f1f1f1",
                    fontWeight: 600,
                    cursor: "pointer",
                    lineHeight: 1.3,
                    "&:hover": { color: "#fff" },
                  }}
                  onClick={() => video.channel_id && navigate(`/channel/${video.channel_id}`)}
                >
                  {video.channel_name}
                </Typography>
                {channel && (
                  <Typography variant="caption" sx={{ color: "#AAAAAA", lineHeight: 1.3 }}>
                    {channel.video_count} video{channel.video_count !== 1 ? "s" : ""} archived
                  </Typography>
                )}
              </Box>
            </Box>

            {/* Action Pills */}
            <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, flexWrap: "wrap" }}>
              {/* Like / Dislike Pill */}
              {(video.like_count != null || video.dislike_count != null) && (
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    bgcolor: "rgba(255, 255, 255, 0.1)",
                    borderRadius: 10,
                    "&:hover": { bgcolor: "rgba(255, 255, 255, 0.2)" },
                    transition: "background-color 0.2s",
                    cursor: "not-allowed"
                  }}
                >
                  {/* Like Button */}
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 1,
                      px: 2,
                      py: 0.75,
                      borderRight: video.dislike_count != null ? "1px solid rgba(255, 255, 255, 0.2)" : "none",
                    }}
                  >
                    <ThumbUpOutlinedIcon fontSize="small" sx={{ color: "#f1f1f1" }} />
                    <Typography variant="body2" sx={{ color: "#f1f1f1", fontWeight: 600 }}>
                      {video.like_count != null ? formatViews(video.like_count, false) : "Like"}
                    </Typography>
                  </Box>

                  {/* Dislike Button */}
                  {video.dislike_count != null && (
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        gap: 1,
                        px: 2,
                        py: 0.75,
                      }}
                    >
                      <ThumbDownOutlinedIcon fontSize="small" sx={{ color: "#f1f1f1" }} />
                      <Typography variant="body2" sx={{ color: "#f1f1f1", fontWeight: 600 }}>
                        {formatViews(video.dislike_count, false)}
                      </Typography>
                    </Box>
                  )}
                </Box>
              )}

              {/* Download Pill */}
              <Box
                component="a"
                href={videoApi.getStreamUrl(video.id)}
                download={`${video.title}.mp4`}
                target="_blank"
                rel="noopener noreferrer"
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 1,
                  px: 2,
                  py: 0.75,
                  bgcolor: "rgba(255, 255, 255, 0.1)",
                  borderRadius: 10,
                  textDecoration: "none",
                  "&:hover": { bgcolor: "rgba(255, 255, 255, 0.2)" },
                  transition: "background-color 0.2s",
                }}
              >
                <DownloadOutlinedIcon fontSize="small" sx={{ color: "#f1f1f1" }} />
                <Typography variant="body2" sx={{ color: "#f1f1f1", fontWeight: 600 }}>
                  Download {video.file_size && `(${formatFileSize(video.file_size)})`}
                </Typography>
              </Box>

              {/* Rearchive Pill */}
              <Box
                onClick={async () => {
                  if (rearchiving) return;
                  if (!window.confirm("Verify availability and re-archive this video? This deletes the current file and queues a fresh download.")) return;
                  
                  setRearchiving(true);
                  setRearchiveMessage(null);
                  setRearchiveError(null);
                  try {
                    const { data } = await videoApi.rearchive(video.id);
                    setRearchiveMessage(data.message || "Video queued for re-archiving");
                    // Force the video object locally to pending so the UI updates to show the giant Pending clock icon
                    setVideo((prev) => ({ ...prev, status: "pending", file_path: null }));
                  } catch (err) {
                    const msg = err.response?.data?.error?.message || err.response?.data?.detail || err.message;
                    setRearchiveError(msg);
                  } finally {
                    setRearchiving(false);
                  }
                }}
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 1,
                  px: 2,
                  py: 0.75,
                  bgcolor: "rgba(255, 255, 255, 0.1)",
                  borderRadius: 10,
                  cursor: "pointer",
                  "&:hover": { bgcolor: "rgba(255, 255, 255, 0.2)" },
                  transition: "background-color 0.2s",
                  opacity: rearchiving ? 0.5 : 1,
                }}
              >
                {rearchiving ? <CircularProgress size={16} sx={{ color: "#f1f1f1" }} /> : <Icon icon="mdi:refresh" width={20} color="#f1f1f1" />}
                <Typography variant="body2" sx={{ color: "#f1f1f1", fontWeight: 600 }}>
                  {rearchiving ? "Checking..." : "Rearchive"}
                </Typography>
              </Box>

              {/* Remove Pill */}
              <Box
                onClick={async () => {
                  if (!window.confirm("Remove this video from archive? This will delete the file from disk.")) return;
                  try {
                    await videoApi.delete(video.id);
                    navigate("/");
                  } catch (err) {
                    alert("Failed to remove video.");
                  }
                }}
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 1,
                  px: 2,
                  py: 0.75,
                  bgcolor: "rgba(255, 255, 255, 0.1)",
                  borderRadius: 10,
                  cursor: "pointer",
                  "&:hover": { bgcolor: "rgba(255, 77, 77, 0.25)" },
                  transition: "background-color 0.2s",
                }}
              >
                <DeleteOutlinedIcon fontSize="small" sx={{ color: "#f1f1f1" }} />
                <Typography variant="body2" sx={{ color: "#f1f1f1", fontWeight: 600 }}>
                  Remove
                </Typography>
              </Box>
            </Box>
          </Box>

          {/* Description box — YouTube-style expandable */}
          <Box
            onClick={() => setShowFullDescription(!showFullDescription)}
            sx={{
              bgcolor: "#272727",
              borderRadius: 2,
              p: 2,
              cursor: "pointer",
              "&:hover": { bgcolor: "#3a3a3a" },
            }}
          >
            {/* Metadata line */}
            <Typography variant="body2" sx={{ color: "#f1f1f1", fontWeight: 600, mb: 1, fontSize: "0.85rem" }}>
              {video.view_count != null ? `${formatViews(video.view_count)} • ` : ""}
              {video.upload_date ? `published ${timeAgo(video.upload_date)} • ` : ""}
              {/* dont show this duration but keep commented {video.duration > 0 && ` • ${formatDuration(video.duration)}`} */}
              {/* {video.file_size && ` • ${formatFileSize(video.file_size)}`} */}
              {video.created_at ? `archived ${timeAgo(video.created_at)}` : ""}
            </Typography>

            <Typography
              variant="body2"
              sx={{
                color: "#e0e0e0",
                whiteSpace: "pre-wrap",
                display: showFullDescription ? "block" : "-webkit-box",
                WebkitLineClamp: showFullDescription ? "none" : 3,
                WebkitBoxOrient: "vertical",
                overflow: showFullDescription ? "visible" : "hidden",
                fontSize: "0.85rem",
                lineHeight: 1.6,
              }}
            >
              {video.description}
            </Typography>
            {!showFullDescription && video.description && video.description.length > 200 && (
              <Typography variant="caption" sx={{ color: "#AAAAAA", fontWeight: 600, mt: 0.5, display: "block" }}>
                Show more
              </Typography>
            )}
            {showFullDescription && (
              <Typography variant="caption" sx={{ color: "#AAAAAA", fontWeight: 600, mt: 1, display: "block" }}>
                Show less
              </Typography>
            )}
          </Box>
        </Box>
      </Box>

      {/* ── Sidebar — Related Videos (YouTube-style list) ── */}
      <Box sx={{ width: { xs: "100%", lg: 402 }, flexShrink: 0, px: { xs: 2, lg: 0 }, pb: 4 }}>
        <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
          {relatedVideos.slice(0, 15).map((v) => (
            <SidebarVideoCard key={v.id} video={v} />
          ))}
        </Box>
      </Box>
    </Box>
  );
}

/* ── Sidebar Video Card (YouTube-style horizontal) ── */
function SidebarVideoCard({ video }) {
  const navigate = useNavigate();
  const thumbnailUrl = video.thumbnail_path
    ? videoApi.getThumbnailUrl(video.id)
    : video.thumbnail_url;

  return (
    <Box
      sx={{
        display: "flex",
        gap: 1,
        cursor: "pointer",
        borderRadius: 1.5,
        p: 0.5,
        "&:hover": { bgcolor: "rgba(255,255,255,0.05)" },
        "&:hover .sidebar-title": { color: "#fff" },
      }}
      onClick={() => navigate(`/watch/${video.id}`)}
    >
      {/* Thumbnail */}
      <Box
        sx={{
          position: "relative",
          width: 168,
          minWidth: 168,
          height: 94,
          bgcolor: "#181818",
          borderRadius: 1.5,
          overflow: "hidden",
        }}
      >
        <Box
          component="img"
          src={thumbnailUrl}
          alt={video.title}
          sx={{ width: "100%", height: "100%", objectFit: "cover" }}
          onError={(e) => { e.target.style.display = "none"; }}
        />
        {video.duration > 0 && (
          <Box
            sx={{
              position: "absolute",
              bottom: 4,
              right: 4,
              bgcolor: "rgba(0,0,0,0.85)",
              color: "#fff",
              px: 0.5,
              py: 0.1,
              borderRadius: 0.5,
              fontSize: 11,
              fontWeight: 600,
              lineHeight: 1.4,
            }}
          >
            {formatDuration(video.duration)}
          </Box>
        )}
      </Box>

      {/* Info */}
      <Box sx={{ flex: 1, minWidth: 0, pt: 0.25 }}>
        <Typography
          className="sidebar-title"
          variant="body2"
          sx={{
            color: "#f1f1f1",
            fontWeight: 500,
            fontSize: "0.8rem",
            lineHeight: 1.4,
            display: "-webkit-box",
            WebkitLineClamp: 2,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
            mb: 0.5,
          }}
        >
          {video.title}
        </Typography>
        <Typography variant="caption" sx={{ color: "#AAAAAA", display: "block", lineHeight: 1.4, fontSize: "0.72rem" }}>
          {video.channel_name}
        </Typography>
        <Typography variant="caption" sx={{ color: "#AAAAAA", fontSize: "0.72rem" }}>
          {video.view_count != null ? `${formatViews(video.view_count)} • ` : ""}
          {timeAgo(video.upload_date || video.created_at)}
        </Typography>
      </Box>
    </Box>
  );
}
