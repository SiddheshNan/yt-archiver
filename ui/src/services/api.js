import api from "@/services/axios.instance";

export const videoApi = {
  list: (page = 1, pageSize = 24, status = null) => {
    const params = { page, page_size: pageSize };
    if (status) params.status = status;
    return api.get("/api/videos", { params });
  },

  get: (id) => api.get(`/api/videos/${id}`),

  getHomeRecommendations: (excludeIds = [], limit = 24) =>
    api.post("/api/videos/recommend/home", { exclude_ids: excludeIds, limit }),

  getRelatedVideos: (id, limit = 20) =>
    api.get(`/api/videos/${id}/related`, { params: { limit } }),

  add: (url) => api.post("/api/videos", { url }),

  addPlaylist: (url) => api.post("/api/videos/playlist", { url }),

  addBatch: (urls) => api.post("/api/videos/batch", { urls }),

  delete: (id) => api.delete(`/api/videos/${id}`),

  rearchive: (id) => api.post(`/api/videos/${id}/rearchive`),

  getStreamUrl: (id) => `${api.defaults.baseURL}/api/videos/${id}/stream`,

  getThumbnailUrl: (id) => `${api.defaults.baseURL}/api/videos/${id}/thumbnail`,

  getSubtitleUrl: (id, lang) => `${api.defaults.baseURL}/api/videos/${id}/subtitles/${encodeURIComponent(lang)}`,

  search: (q, channelId = null, page = 1, pageSize = 24) => {
    const params = { q, page, page_size: pageSize };
    if (channelId) params.channel_id = channelId;
    return api.get("/api/search", { params });
  },
};

export const channelApi = {
  list: (page = 1, pageSize = 50) =>
    api.get("/api/channels", { params: { page, page_size: pageSize } }),

  get: (id) => api.get(`/api/channels/${id}`),

  getVideos: (id, page = 1, pageSize = 24) =>
    api.get(`/api/channels/${id}/videos`, { params: { page, page_size: pageSize } }),

  getAvatar: (id) => api.get(`/api/channels/${id}/avatar`),

  archive: (url) => api.post("/api/channels/archive", { url }),
};

export const downloadsApi = {
  queueStatus: () => api.get("/api/downloads/queue"),
};

export const healthApi = {
  check: () => api.get("/api/health"),
};
