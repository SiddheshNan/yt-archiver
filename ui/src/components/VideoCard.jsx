import { useNavigate } from "react-router-dom";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import ChannelAvatar from "@/components/ChannelAvatar";
import { videoApi } from "@/services/api";
import { formatDuration, timeAgo, formatViews } from "@/utils/format";

export default function VideoCard({ video }) {
  const navigate = useNavigate();

  const thumbnailUrl = video.thumbnail_path
    ? videoApi.getThumbnailUrl(video.id)
    : video.thumbnail_url;

  return (
    <Box
      sx={{
        cursor: "pointer",
        borderRadius: 2,
        overflow: "hidden",
        transition: "all 0.2s ease",
        "&:hover .video-title": { color: "#fff" },
      }}
      onClick={() => navigate(`/watch/${video.id}`)}
    >
      {/* Thumbnail */}
      <Box
        sx={{
          position: "relative",
          width: "100%",
          paddingTop: "56.25%",
          bgcolor: "#181818",
          borderRadius: 2,
          overflow: "hidden",
        }}
      >
        <Box
          component="img"
          src={thumbnailUrl}
          alt={video.title}
          sx={{
            position: "absolute",
            top: 0, left: 0,
            width: "100%",
            height: "100%",
            objectFit: "cover",
            borderRadius: 2,
          }}
          onError={(e) => { e.target.style.display = "none"; }}
        />
        {/* Duration badge */}
        {video.duration > 0 && (
          <Box
            sx={{
              position: "absolute",
              bottom: 6,
              right: 6,
              bgcolor: "rgba(0,0,0,0.85)",
              color: "#fff",
              px: 0.6,
              py: 0.15,
              borderRadius: 0.5,
              fontSize: 12,
              fontWeight: 600,
              lineHeight: 1.4,
            }}
          >
            {formatDuration(video.duration)}
          </Box>
        )}
        {/* Status badge */}
        {video.status && video.status !== "completed" && (
          <Box
            sx={{
              position: "absolute",
              top: 6,
              left: 6,
              bgcolor:
                video.status === "failed" ? "#ff4444"
                : video.status === "downloading" ? "#3EA6FF"
                : "#888",
              color: "#fff",
              px: 1,
              py: 0.3,
              borderRadius: 0.5,
              fontSize: 11,
              fontWeight: 600,
              textTransform: "uppercase",
            }}
          >
            {video.status}
          </Box>
        )}
      </Box>

      {/* Info row — YouTube-style: avatar | text */}
      <Box sx={{ display: "flex", gap: 1.5, pt: 1.2 }}>
        {/* Channel Avatar */}
        <ChannelAvatar
          channelId={video.channel_id}
          channelName={video.channel_name}
          size={36}
          sx={{ mt: 0.2 }}
          onClick={(e) => {
            e.stopPropagation();
            if (video.channel_id) navigate(`/channel/${video.channel_id}`);
          }}
        />

        {/* Text */}
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography
            className="video-title"
            variant="body2"
            sx={{
              color: "#f1f1f1",
              fontWeight: 600,
              lineHeight: 1.3,
              display: "-webkit-box",
              WebkitLineClamp: 2,
              WebkitBoxOrient: "vertical",
              overflow: "hidden",
              mb: 0.4,
              fontSize: "0.9rem",
            }}
          >
            {video.title}
          </Typography>
          <Typography
            variant="caption"
            sx={{
              color: "#AAAAAA",
              cursor: "pointer",
              "&:hover": { color: "#fff" },
              display: "block",
              lineHeight: 1.4,
              fontSize: "0.78rem",
            }}
            onClick={(e) => {
              e.stopPropagation();
              if (video.channel_id) navigate(`/channel/${video.channel_id}`);
            }}
          >
            {video.channel_name}
          </Typography>
          <Typography variant="caption" sx={{ color: "#AAAAAA", fontSize: "0.78rem" }}>
            {video.view_count != null ? `${formatViews(video.view_count)} • ` : ""}
            {timeAgo(video.upload_date)}
          </Typography>
        </Box>
      </Box>
    </Box>
  );
}
