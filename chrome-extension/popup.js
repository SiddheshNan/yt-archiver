const apiUrlInput = document.getElementById("apiUrl");
const cfClientIdInput = document.getElementById("cfClientId");
const cfClientSecretInput = document.getElementById("cfClientSecret");
const saveBtn = document.getElementById("saveBtn");
const statusEl = document.getElementById("status");

// Load saved config on popup open
chrome.storage.sync.get(["archiverApiUrl", "cfClientId", "cfClientSecret"], (data) => {
  if (data.archiverApiUrl) apiUrlInput.value = data.archiverApiUrl;
  if (data.cfClientId) cfClientIdInput.value = data.cfClientId;
  if (data.cfClientSecret) cfClientSecretInput.value = data.cfClientSecret;
});

saveBtn.addEventListener("click", () => {
  let url = apiUrlInput.value.trim();
  let clientId = cfClientIdInput.value.trim();
  let clientSecret = cfClientSecretInput.value.trim();

  if (!url) {
    statusEl.style.color = "#ff4444";
    statusEl.textContent = "Please enter an API URL";
    return;
  }
  // Strip trailing slash
  url = url.replace(/\/+$/, "");

  const payload = {
    archiverApiUrl: url,
    cfClientId: clientId,
    cfClientSecret: clientSecret
  };

  chrome.storage.sync.set(payload, () => {
    statusEl.style.color = "#4caf50";
    statusEl.textContent = "Saved ✓";
    setTimeout(() => (statusEl.textContent = ""), 2000);
  });
});
