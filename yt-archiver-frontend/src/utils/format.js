/**
 * Format duration in seconds to mm:ss or hh:mm:ss
 */
export function formatDuration(seconds) {
  if (!seconds || seconds <= 0) return "0:00";

  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);

  if (h > 0) {
    return `${h}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  }
  return `${m}:${s.toString().padStart(2, "0")}`;
}

/**
 * Format relative time (e.g. "3 days ago")
 */
export function timeAgo(dateString) {
  if (!dateString) return "";
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);
  const diffMonths = Math.floor(diffDays / 30);
  const diffYears = Math.floor(diffDays / 365);

  if (diffYears > 0) return `${diffYears} year${diffYears > 1 ? "s" : ""} ago`;
  if (diffMonths > 0) return `${diffMonths} month${diffMonths > 1 ? "s" : ""} ago`;
  if (diffDays > 0) return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`;
  if (diffHours > 0) return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`;
  if (diffMins > 0) return `${diffMins} minute${diffMins > 1 ? "s" : ""} ago`;
  return "just now";
}

/**
 * Format view-friendly file size
 */
export function formatFileSize(bytes) {
  if (!bytes) return "";
  const units = ["B", "KB", "MB", "GB"];
  let i = 0;
  let size = bytes;
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024;
    i++;
  }
  return `${size.toFixed(1)} ${units[i]}`;
}

/**
 * Format view count like YouTube (e.g. "1.2M views", "340K views")
 */
export function formatViews(count, showViews = true) {
  if (count == null) return "";
  if (count >= 1_000_000_000) return `${(count / 1_000_000_000).toFixed(1)}B ${showViews ? "views" : ""}`;
  if (count >= 1_000_000) return `${(count / 1_000_000).toFixed(1)}M ${showViews ? "views" : ""}`;
  if (count >= 1_000) return `${(count / 1_000).toFixed(1)}K ${showViews ? "views" : ""}`;
  return `${count} ${showViews ? "views" : ""}`;
}
