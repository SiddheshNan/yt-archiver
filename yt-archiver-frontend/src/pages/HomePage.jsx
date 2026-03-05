import { useState, useEffect } from "react";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import VideoGrid from "@/components/VideoGrid";
import { videoApi } from "@/services/api";

export default function HomePage() {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const pageSize = 24;

  const fetchVideos = async (excludeIds = []) => {
    try {
      setLoading(true);
      const { data } = await videoApi.getHomeRecommendations(excludeIds, pageSize);
      if (excludeIds.length === 0) {
        setVideos(data);
      } else {
        setVideos((prev) => [...prev, ...data]);
      }
    } catch (err) {
      console.error("Failed to fetch videos:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVideos([]);
  }, []);

  const handleLoadMore = () => {
    const excludeIds = videos.map(v => v.id);
    fetchVideos(excludeIds);
  };

  // If the last fetch returned fewer than pageSize, assume we've hit the end
  const hasMore = videos.length > 0 && videos.length % pageSize === 0;

  return (
    <Box sx={{ px: { xs: 2, sm: 3, md: 4 }, py: 3 }}>
      {loading && videos.length === 0 ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 10 }}>
          <CircularProgress sx={{ color: "#fff" }} />
        </Box>
      ) : videos.length === 0 ? (
        <Box sx={{ textAlign: "center", py: 10 }}>
          <Typography variant="h5" sx={{ color: "#aaa", mb: 1 }}>
            No videos yet
          </Typography>
          <Typography variant="body2" sx={{ color: "#717171" }}>
            Add your first video using the + button in the top bar
          </Typography>
        </Box>
      ) : (
        <>
          <VideoGrid videos={videos} />

          {hasMore && (
            <Box sx={{ display: "flex", justifyContent: "center", mt: 4, mb: 2 }}>
              <Button
                variant="outlined"
                onClick={handleLoadMore}
                disabled={loading}
                sx={{
                  color: "#3EA6FF",
                  borderColor: "rgba(62,166,255,0.5)",
                  px: 4,
                  "&:hover": { borderColor: "#3EA6FF", bgcolor: "rgba(62,166,255,0.1)" },
                }}
              >
                {loading ? <CircularProgress size={20} sx={{ color: "#3EA6FF" }} /> : "Load More"}
              </Button>
            </Box>
          )}
        </>
      )}
    </Box>
  );
}
