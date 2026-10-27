# Security

YT Archiver has no users or login. Anyone who can reach its port can add, watch and delete videos.

## Keep it private

Pick one:

- **Local network only.** Don't forward the port on your router.
- **A VPN** such as Tailscale or WireGuard, so only your devices can reach it.
- **An access proxy** such as Cloudflare Access (with Cloudflare Tunnel) in front of it. The [extension](/docs/extension) can send a Cloudflare Access service token, so it keeps working.

## CORS

The default configs allow any origin (`"*"` in `server.cors_origins`) so the extension can call the API from youtube.com. If you put YT Archiver on the internet behind an access proxy, list only the origins you use.

## Cookies

A `cookies.txt` in the config folder is a logged-in YouTube session. Use a throwaway account, and leave the file out of anything you share.

## Reporting a vulnerability

See [SECURITY.md](https://github.com/SiddheshNan/yt-archiver/blob/main/SECURITY.md).
