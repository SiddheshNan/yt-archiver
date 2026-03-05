import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import { Icon } from "@iconify/react";
import VideoGrid from "@/components/VideoGrid";
import ChannelAvatar from "@/components/ChannelAvatar";
import { channelApi } from "@/services/api";

export default function ChannelPage() {
  const { id } = useParams();
  const [channel, setChannel] = useState(null);
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 24;

  useEffect(() => {
    const fetchChannel = async () => {
      try {
        setLoading(true);
        const [channelRes, videosRes] = await Promise.all([
          channelApi.get(id),
          channelApi.getVideos(id, 1, pageSize),
        ]);
        setChannel(channelRes.data);
        setVideos(videosRes.data.items);
        setTotal(videosRes.data.total);
      } catch (err) {
        console.error("Failed to fetch channel:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchChannel();
  }, [id]);

  const handleLoadMore = async () => {
    const nextPage = page + 1;
    setPage(nextPage);
    try {
      const { data } = await channelApi.getVideos(id, nextPage, pageSize);
      setVideos((prev) => [...prev, ...data.items]);
    } catch (err) {
      console.error("Failed to load more:", err);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 10 }}>
        <CircularProgress sx={{ color: "#fff" }} />
      </Box>
    );
  }

  if (!channel) {
    return (
      <Box sx={{ textAlign: "center", py: 10 }}>
        <Typography variant="h5" sx={{ color: "#aaa" }}>Channel not found</Typography>
      </Box>
    );
  }

  const hasMore = videos.length < total;

  return (
    <Box>
      {/* Channel Header */}
      <Box
        sx={{
          px: { xs: 2, sm: 4, md: 6 },
          py: 3,
          borderBottom: "1px solid rgba(255,255,255,0.1)",
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 3 }}>
          <ChannelAvatar
            channelId={id}
            channelName={channel.name}
            size={80}
          />
          <Box>
            <Typography variant="h5" sx={{ color: "#fff", fontWeight: 700, mb: 0.5 }}>
              {channel.name}
            </Typography>
            <Typography variant="body2" sx={{ color: "#AAAAAA" }}>
              {channel.video_count} video{channel.video_count !== 1 ? "s" : ""} archived
            </Typography>
            {channel.description && (
              <Typography variant="body2" sx={{ color: "#717171", mt: 0.5, maxWidth: 600 }}>
                {channel.description}
              </Typography>
            )}
          </Box>
        </Box>
      </Box>

      {/* Videos */}
      <Box sx={{ px: { xs: 2, sm: 3, md: 4 }, py: 3 }}>
        <Typography variant="subtitle1" sx={{ color: "#f1f1f1", fontWeight: 600, mb: 2.5 }}>
          Videos
        </Typography>

        {videos.length === 0 ? (
          <Typography sx={{ color: "#717171", py: 4 }}>No videos archived yet</Typography>
        ) : (
          <>
            <VideoGrid videos={videos} />
            {hasMore && (
              <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}>
                <Button
                  variant="outlined"
                  onClick={handleLoadMore}
                  sx={{
                    color: "#3EA6FF",
                    borderColor: "rgba(62,166,255,0.5)",
                    px: 4,
                    "&:hover": { borderColor: "#3EA6FF", bgcolor: "rgba(62,166,255,0.1)" },
                  }}
                >
                  Load More
                </Button>
              </Box>
            )}
          </>
        )}
      </Box>
    </Box>
  );
}
