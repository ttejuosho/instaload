# Instagram video downloader

Requires Python 3.10 or later.

```powershell
python -m pip install -r requirements.txt
python download_instagram.py "https://www.instagram.com/reel/SHORTCODE/"
```

Videos are saved in `downloads/<owner_handle>/`. The script reads the owner's
handle from Instagram and creates the folder automatically, including for
individual URLs. Your existing `downloads/test.and.tutor/` folder is reused,
and matching files there are skipped. Supports Reel, `/p/`, and `/tv/` URLs,
including videos in carousel posts. Photos are skipped. Existing files are
skipped. Pass multiple URLs separated by spaces, or `--output PATH` to choose
a base destination (videos go under `PATH/<owner_handle>/`). The script exits with status 1 if any requested post fails or
contains no videos.

## Download by handle

```powershell
python download_instagram.py --profile HANDLE
```

Scans the account's posts and Reels and saves videos to `downloads/HANDLE`.
You can also use `--profile "@HANDLE"`. Photos are skipped, and posts appearing
in both lists are processed once. This downloads the videos Instagram makes
available to the session; it does not include Stories or Highlights.
If a scan fails, the script reports an incomplete download and exits with status 1.
Rerun the command to retry, skipping existing files.

For accounts that require login:

```powershell
python -m instaloader --login YOUR_USERNAME
python download_instagram.py --profile TARGET_HANDLE --username YOUR_USERNAME
```

`TARGET_HANDLE` is the account to download; `YOUR_USERNAME` is your login account.
Profile iteration uses Instaloader's documented `get_posts()` and `get_reels()`:
https://instaloader.github.io/module/structures.html

## Login when needed

Instagram may require login even for public posts. Create a saved session with
Instaloader's interactive login, then use it with this script:

```powershell
python -m instaloader --login YOUR_USERNAME
python download_instagram.py --username YOUR_USERNAME "https://www.instagram.com/reel/SHORTCODE/"
```

For a session saved in a custom location, also pass `--session-file PATH`.
Only load session files you trust; they contain authentication information.
Private posts require an account with access. Instagram rate limits or access
challenges can prevent downloads; the script cannot bypass these restrictions.
Stories, profile URLs, and share redirect URLs are not supported as URL inputs;
use `--profile HANDLE` for an account or copy a direct post or Reel link.

Library documentation: https://instaloader.github.io/
