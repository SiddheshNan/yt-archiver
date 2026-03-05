import { useState, useEffect } from "react";
import Avatar from "@mui/material/Avatar";
import { channelApi } from "@/services/api";

// Simple in-memory cache so we don't re-fetch the same avatar
const avatarCache = {};

/**
 * Channel avatar that lazy-loads the real YouTube profile picture.
 * Falls back to a letter avatar while loading or if unavailable.
 */
export default function ChannelAvatar({ channelId, channelName, size = 36, onClick, sx = {} }) {
  const [avatarUrl, setAvatarUrl] = useState(avatarCache[channelId] || null);

  useEffect(() => {
    if (!channelId || avatarUrl) return;

    // Check cache first
    if (avatarCache[channelId]) {
      setAvatarUrl(avatarCache[channelId]);
      return;
    }

    let cancelled = false;
    channelApi.getAvatar(channelId)
      .then(({ data }) => {
        if (!cancelled && data.avatar_url) {
          avatarCache[channelId] = data.avatar_url;
          setAvatarUrl(data.avatar_url);
        }
      })
      .catch(() => {});

    return () => { cancelled = true; };
  }, [channelId]);

  return (
    <Avatar
      src={avatarUrl}
      alt={channelName}
      onClick={onClick}
      sx={{
        width: size,
        height: size,
        bgcolor: "#3EA6FF",
        fontSize: size * 0.4,
        fontWeight: 700,
        cursor: onClick ? "pointer" : "default",
        ...sx,
      }}
    >
      {channelName?.[0]?.toUpperCase()}
    </Avatar>
  );
}
