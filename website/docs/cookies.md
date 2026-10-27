# Cookies and 1080p

When you download a lot, YouTube may decide your server is a bot. It then offers only low-quality formats, often 360p, or asks to "sign in to confirm you're not a bot". Logging yt-dlp in with cookies fixes this.

::: warning Use a throwaway account
Cookies give full access to the account they come from, and heavy downloading can get an account flagged. Don't use your main Google account.
:::

## Cookies file (Docker and servers)

1. Log in to YouTube in a browser with the account you want to use.
2. Export the cookies in Netscape format with an extension such as "Get cookies.txt LOCALLY".
3. Save the file as `cookies.txt` in the config folder: `data/config/cookies.txt` with Docker Compose, `runtime/config/cookies.txt` otherwise.
4. Point the config at it:

   ```yaml
   downloads:
     cookies_file: "runtime/config/cookies.txt"
   ```

   The path is the same in Docker, because `data/` is mounted at `/app/runtime`. Restart YT Archiver.

YouTube rotates cookies, so expect to export them again from time to time.

## From a browser (local use)

When YT Archiver runs on the same machine as your browser, yt-dlp can read the browser's cookies directly:

```yaml
downloads:
  browser_cookies: "chrome"    # or firefox, safari, edge, brave
```

`cookies_file` wins when both are set and the file exists.
