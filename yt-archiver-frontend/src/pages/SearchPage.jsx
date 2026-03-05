import { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import ChannelAvatar from "@/components/ChannelAvatar";
import { videoApi } from "@/services/api";
import { formatDuration, timeAgo, formatViews } from "@/utils/format";

export default function SearchPage() {
  const [searchParams] = useSearchParams();
  const query = searchParams.get("q") || "";
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 20;

  useEffect(() => {
    if (!query) return;
    setPage(1);
    setResults([]);
    fetchResults(query, 1);
  }, [query]);

  const fetchResults = async (q, pageNum) => {
    try {
      setLoading(true);
      const { data } = await videoApi.search(q, null, pageNum, pageSize);
      if (pageNum === 1) {
        setResults(data.items);
      } else {
        setResults((prev) => [...prev, ...data.items]);
      }
      setTotal(data.total);
    } catch (err) {
      console.error("Search failed:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadMore = () => {
    const nextPage = page + 1;
    setPage(nextPage);
    fetchResults(query, nextPage);
  };

  const hasMore = results.length < total;

  if (!query) {
    return (
      <Box sx={{ textAlign: "center", py: 10 }}>
        <Typography variant="h6" sx={{ color: "#aaa" }}>Enter a search query</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1050, mx: "auto", px: { xs: 2, sm: 3 }, py: 2.5 }}>
      <Helmet>
        <title>{query ? `${query} - Search` : "Search"} - YouTube Archiver</title>
        <meta name="description" content={`Search results for "${query}" in your video archive`} />
      </Helmet>
      {loading && results.length === 0 ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
          <CircularProgress sx={{ color: "#fff" }} />
        </Box>
      ) : results.length === 0 ? (
        <Box sx={{ textAlign: "center", py: 8 }}>
          <Typography variant="h6" sx={{ color: "#aaa", mb: 1 }}>No results found</Typography>
          <Typography variant="body2" sx={{ color: "#717171" }}>
            Try different keywords or check your spelling
          </Typography>
        </Box>
      ) : (
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {results.map((video) => (
            <SearchResultCard key={video.id} video={video} />
          ))}
          {hasMore && (
            <Box sx={{ display: "flex", justifyContent: "center", mt: 2 }}>
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
        </Box>
      )}
    </Box>
  );
}

/* ── YouTube-style horizontal search result card ── */
function SearchResultCard({ video }) {
  const navigate = useNavigate();

  const thumbnailUrl = video.thumbnail_path
    ? videoApi.getThumbnailUrl(video.id)
    : video.thumbnail_url;

  return (
    <Box
      sx={{
        display: "flex",
        gap: 2,
        cursor: "pointer",
        borderRadius: 2,
        "&:hover .search-title": { color: "#fff" },
      }}
      onClick={() => navigate(`/watch/${video.id}`)}
    >
      {/* Thumbnail */}
      <Box
        sx={{
          position: "relative",
          width: { xs: 160, sm: 360 },
          minWidth: { xs: 160, sm: 360 },
          height: { xs: 90, sm: 202 },
          bgcolor: "#181818",
          borderRadius: 2,
          overflow: "hidden",
          flexShrink: 0,
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
              bottom: 6,
              right: 6,
              bgcolor: "rgba(0,0,0,0.85)",
              color: "#fff",
              px: 0.6,
              py: 0.15,
              borderRadius: 0.5,
              fontSize: 12,
              fontWeight: 600,
            }}
          >
            {formatDuration(video.duration)}
          </Box>
        )}
      </Box>

      {/* Info */}
      <Box sx={{ flex: 1, minWidth: 0, py: { xs: 0, sm: 0.5 } }}>
        <Typography
          className="search-title"
          sx={{
            color: "#f1f1f1",
            fontWeight: 500,
            fontSize: { xs: "0.85rem", sm: "1.1rem" },
            lineHeight: 1.3,
            display: "-webkit-box",
            WebkitLineClamp: 2,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
            mb: 0.6,
          }}
        >
          {video.title}
        </Typography>

        <Typography variant="caption" sx={{ color: "#AAAAAA", display: "block", mb: 1, fontSize: "0.75rem" }}>
          {video.view_count != null ? `${formatViews(video.view_count)} • ` : ""}
          {timeAgo(video.upload_date || video.created_at)}
          {video.duration > 0 && ` • ${formatDuration(video.duration)}`}
        </Typography>

        <Box
          sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1, cursor: "pointer" }}
          onClick={(e) => {
            e.stopPropagation();
            if (video.channel_id) navigate(`/channel/${video.channel_id}`);
          }}
        >
          <ChannelAvatar
            channelId={video.channel_id}
            channelName={video.channel_name}
            size={24}
          />
          <Typography
            variant="caption"
            sx={{ color: "#AAAAAA", "&:hover": { color: "#fff" }, fontSize: "0.75rem" }}
          >
            {video.channel_name}
          </Typography>
        </Box>

        {/* Description snippet — only on larger screens */}
        {video.description && (
          <Typography
            variant="caption"
            sx={{
              color: "#717171",
              display: { xs: "none", sm: "-webkit-box" },
              WebkitLineClamp: 2,
              WebkitBoxOrient: "vertical",
              overflow: "hidden",
              fontSize: "0.75rem",
              lineHeight: 1.5,
            }}
          >
            {video.description}
          </Typography>
        )}
      </Box>
    </Box>
  );
}
