# Security

## Reporting a vulnerability

Please don't open a public issue. Report it privately through GitHub instead: go to the repository's **Security** tab and choose **Report a vulnerability**.

Include what you found, how to reproduce it and which version you tested. You'll get a reply within a few days, and once a fix is released you'll be credited unless you'd rather not be.

## Before you expose it

YT Archiver has no login of its own: anyone who can reach it can add, watch and delete videos. Keep it on a private network, or put it behind a VPN or an access proxy such as Cloudflare Access. The Chrome extension can send Cloudflare Access service-token headers for that case.

A `cookies.txt` in the config folder gives access to the YouTube account it came from. Use a throwaway account, and keep the file out of backups you share.

## Supported versions

YT Archiver is pre-release. Fixes go into the latest release only.
