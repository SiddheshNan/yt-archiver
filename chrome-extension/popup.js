const apiUrlInput = document.getElementById("apiUrl");
const saveBtn = document.getElementById("saveBtn");
const statusEl = document.getElementById("status");

// Load saved URL on popup open
chrome.storage.sync.get("archiverApiUrl", ({ archiverApiUrl }) => {
  if (archiverApiUrl) apiUrlInput.value = archiverApiUrl;
});

saveBtn.addEventListener("click", () => {
  let url = apiUrlInput.value.trim();
  if (!url) {
    statusEl.style.color = "#ff4444";
    statusEl.textContent = "Please enter a URL";
    return;
  }
  // Strip trailing slash
  url = url.replace(/\/+$/, "");

  chrome.storage.sync.set({ archiverApiUrl: url }, () => {
    statusEl.style.color = "#4caf50";
    statusEl.textContent = "Saved ✓";
    setTimeout(() => (statusEl.textContent = ""), 2000);
  });
});
