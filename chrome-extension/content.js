/* ── YT Archiver Content Script ──
 * Injects "Archive" buttons on YouTube:
 *   - Watch page   → Archives single video   (POST /api/videos)
 *   - Channel page → Archives entire channel  (POST /api/channels/archive)
 *   - Playlist page → Archives entire playlist (POST /api/videos/playlist)
 */

(() => {
  "use strict";
  console.log("YT-Archiver: Content script initialized.");

  const ARCHIVE_SVG = `<svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v3.01c0 .72.43 1.34 1 1.69V20c0 1.1 1.1 2 2 2h14c.9 0 2-.9 2-2V8.7c.57-.35 1-.97 1-1.69V4c0-1.1-.9-2-2-2zm-5 12H9v-2h6v2zm5-7H4V4h16v3z"/></svg>`;

  // ── Detect current page type ───────────────────────────────────────
  function getPageType() {
    const path = window.location.pathname;
    if (path === "/watch") return "video";
    if (path === "/playlist") return "playlist";
    if (
      path.startsWith("/@") ||
      path.startsWith("/channel/") ||
      path.startsWith("/c/") ||
      path.startsWith("/user/")
    ) return "channel";
    return null;
  }

  // ── Map page type → API endpoint, label, success message ──────────
  function getConfig(pageType) {
    switch (pageType) {
      case "video":
        return {
          endpoint: "/api/videos",
          label: "Archive",
          sending: "Sending…",
          done: "Archived",
          duplicate: "Archived",
          successMsg: "Video sent for archival!",
          duplicateMsg: "This video is already archived!",
        };
      case "channel":
        return {
          endpoint: "/api/channels/archive",
          label: "Archive Channel",
          sending: "Archiving…",
          done: "Channel Archived",
          duplicate: "Archived",
          successMsg: "Channel sent for archival! All videos will be downloaded.",
          duplicateMsg: "This channel is already archived!",
        };
      case "playlist":
        return {
          endpoint: "/api/videos/playlist",
          label: "Archive Playlist",
          sending: "Archiving…",
          done: "Playlist Archived",
          duplicate: "Archived",
          successMsg: "Playlist sent for archival! All videos will be downloaded.",
          duplicateMsg: "This playlist is already archived!",
        };
      default:
        return null;
    }
  }

  // ── Find the right container to inject into ────────────────────────
  function findInjectionTarget(pageType) {
    if (pageType === "video") {
      return (
        document.querySelector("#top-level-buttons-computed") ||
        document.querySelector("ytd-menu-renderer.ytd-watch-metadata #top-level-buttons-computed") ||
        document.querySelector("ytd-watch-metadata #actions-inner #menu #top-level-buttons-computed")
      );
    }

    if (pageType === "channel") {
      // Modern YouTube channel layout uses yt-flexible-actions-view-model
      return (
        document.querySelector("#page-header yt-flexible-actions-view-model") ||
        document.querySelector("yt-flexible-actions-view-model") ||
        document.querySelector("#channel-header #buttons")
      );
    }

    if (pageType === "playlist") {
      // Playlist header also uses yt-flexible-actions-view-model
      return (
        document.querySelector("ytd-playlist-header-renderer yt-flexible-actions-view-model") ||
        document.querySelector("ytd-playlist-header-renderer ytd-menu-renderer") ||
        document.querySelector("yt-flexible-actions-view-model")
      );
    }

    return null;
  }

  // ── Create the button element ──────────────────────────────────────
  function createButton(config, pageType) {
    const btn = document.createElement("button");
    btn.className = "yta-archive-btn";
    btn.dataset.pageType = pageType;
    btn.innerHTML = `${ARCHIVE_SVG}<span>${config.label}</span>`;
    btn.title = `Send to YT Archiver`;
    btn.addEventListener("click", () => handleArchive(pageType));
    return btn;
  }

  // ── Inject button ─────────────────────────────────────────────────
  function injectButton() {
    const pageType = getPageType();
    if (!pageType) return;

    // Don't double-inject
    if (document.querySelector(`.yta-archive-btn[data-page-type="${pageType}"]`)) {
      return;
    }

    const config = getConfig(pageType);
    if (!config) return;

    const target = findInjectionTarget(pageType);
    if (!target) {
      console.log(`YT-Archiver: Could not find injection target for ${pageType}. Waiting for DOM mutation...`);
      return;
    }

    console.log(`YT-Archiver: Injecting button into target for ${pageType}`);
    const btn = createButton(config, pageType);
    target.appendChild(btn);

    // If it's a watch page, immediately check if it's already archived
    if (pageType === "video") {
      checkArchiveStatus(btn, window.location.href);
    }
  }

  // ── Check if already archived ─────────────────────────────────────
  async function checkArchiveStatus(btn, currentUrl) {
    try {
      const { archiverApiUrl, cfClientId, cfClientSecret } = await chrome.storage.sync.get(["archiverApiUrl", "cfClientId", "cfClientSecret"]);
      if (!archiverApiUrl) return;

      const urlObj = new URL(currentUrl);
      const videoId = urlObj.searchParams.get("v");
      if (!videoId) return;

      const headers = {};
      if (cfClientId) headers["CF-Access-Client-Id"] = cfClientId;
      if (cfClientSecret) headers["CF-Access-Client-Secret"] = cfClientSecret;

      // URL encode the videoId just in case
      const res = await fetch(`${archiverApiUrl}/api/videos/check?v=${encodeURIComponent(videoId)}`, {
        method: "GET",
        headers: headers,
      });

      if (res.ok) {
        const data = await res.json();
        if (data.is_archived) {
          btn.classList.add("yta-done");
          
          const config = getConfig("video");
          if (data.status === "pending") {
             btn.querySelector("span").textContent = "Archiving…";
          } else if (data.status === "failed") {
             btn.querySelector("span").textContent = "Failed";
             btn.classList.add("yta-error");
             btn.classList.remove("yta-done");
          } else {
             btn.querySelector("span").textContent = config.done;
          }
           // Disable the button since it's already archived
          // btn.disabled = true; // Optional, might want to allow re-trigger or at least keep the appearance
        }
      }
    } catch (err) {
      console.warn("YT-Archiver: Failed to check archive status", err);
    }
  }

  // ── Handle archive click ──────────────────────────────────────────
  async function handleArchive(pageType) {
    console.log(`YT-Archiver: Archive button clicked for pageType: ${pageType}`);
    
    const btn = document.querySelector(`.yta-archive-btn[data-page-type="${pageType}"]`);
    if (!btn || btn.classList.contains("yta-sending")) return;

    const config = getConfig(pageType);
    const currentUrl = window.location.href;

    // Get configured API URL and Optional Cloudflare Auth Tokens
    const { archiverApiUrl, cfClientId, cfClientSecret } = await chrome.storage.sync.get(["archiverApiUrl", "cfClientId", "cfClientSecret"]);
    console.log(`YT-Archiver: Loaded configured API URL: ${archiverApiUrl}`);
    
    if (!archiverApiUrl) {
      alert("YT Archiver: Please set your Archiver API URL in the extension popup first.");
      return;
    }

    btn.classList.add("yta-sending");
    btn.querySelector("span").textContent = config.sending;

    try {
      const headers = { "Content-Type": "application/json" };
      if (cfClientId) headers["CF-Access-Client-Id"] = cfClientId;
      if (cfClientSecret) headers["CF-Access-Client-Secret"] = cfClientSecret;

      const res = await fetch(`${archiverApiUrl}${config.endpoint}`, {
        method: "POST",
        headers: headers,
        body: JSON.stringify({ url: currentUrl }),
      });

      const data = await res.json();

      if (res.ok) {
        btn.classList.remove("yta-sending");
        btn.classList.add("yta-done");
        btn.querySelector("span").textContent = config.done;
        alert(config.successMsg);
      } else if (res.status === 409) {
        btn.classList.remove("yta-sending");
        btn.classList.add("yta-done");
        btn.querySelector("span").textContent = config.duplicate;
        alert(config.duplicateMsg);
      } else {
        const msg = data?.detail?.message || data?.detail || "Unknown error";
        throw new Error(msg);
      }
    } catch (err) {
      btn.classList.remove("yta-sending");
      btn.classList.add("yta-error");
      btn.querySelector("span").textContent = "Failed";
      alert(`YT Archiver Error: ${err.message}`);

      setTimeout(() => {
        btn.classList.remove("yta-error");
        btn.querySelector("span").textContent = config.label;
      }, 3000);
    }
  }

  // ── Watch for YouTube SPA navigation ──────────────────────────────

  function tryInject() {
    // Remove stale buttons
    document.querySelectorAll(".yta-archive-btn").forEach((el) => el.remove());
    injectButton();
  }

  // YouTube fires this custom event on SPA navigations
  window.addEventListener("yt-navigate-finish", () => {
    setTimeout(tryInject, 800);
  });

  // MutationObserver as fallback — catches late DOM rebuilds
  const observer = new MutationObserver(() => {
    const pageType = getPageType();
    if (!pageType) return;
    if (document.querySelector(`.yta-archive-btn[data-page-type="${pageType}"]`)) return;
    injectButton();
  });

  observer.observe(document.body, { childList: true, subtree: true });

  // Initial injection on first load
  if (getPageType()) {
    setTimeout(tryInject, 1000);
  }
})();
