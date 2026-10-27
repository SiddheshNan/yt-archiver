# Chrome extension

The extension adds archive buttons to YouTube and shows whether the video you're watching is already in your archive. It works in Chrome and other Chromium browsers.

## Install

1. Download `yt-archiver-extension.zip` from the [latest release](https://github.com/SiddheshNan/yt-archiver/releases) and unzip it, or use the `extension/` folder of the repository.
2. Open `chrome://extensions` and turn on **Developer mode**.
3. Click **Load unpacked** and choose the folder.

## Set it up

Click the extension's icon and enter your instance URL, for example `http://192.168.1.10:8000` or `https://archive.example.com`. Click **Save**.

If YT Archiver sits behind Cloudflare Access, create a service token in Cloudflare and enter its client ID and secret. The extension sends them as `CF-Access-Client-Id` and `CF-Access-Client-Secret` headers.

## Use it

The extension adds one button, depending on the page: **Archive** on a video, **Archive Channel** on a channel and **Archive Playlist** on a playlist. On a video that is already in your archive, the button says **Archived**.
