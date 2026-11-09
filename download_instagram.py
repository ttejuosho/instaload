"""Download videos from Instagram URLs or a profile handle."""

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


def shortcode_from_url(value: str) -> str:
    """Validate a post URL and extract its case-sensitive shortcode."""
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in {
        "instagram.com", "www.instagram.com", "m.instagram.com"
    }:
        raise argparse.ArgumentTypeError("Use a full https://www.instagram.com/ URL.")
    match = re.fullmatch(r"/(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)/?", parsed.path)
    if not match:
        raise argparse.ArgumentTypeError("Expected an Instagram Reel or post URL.")
    return match.group(1)


def profile_handle(value: str) -> str:
    value = value.removeprefix("@")
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9._]{0,29}", value):
        raise argparse.ArgumentTypeError("Use an Instagram handle, e.g. @example.")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="*", type=shortcode_from_url, metavar="URL")
    parser.add_argument("--profile", type=profile_handle, help="Download a handle's posts and Reels")
    parser.add_argument("-o", "--output", type=Path, default=Path("downloads"),
                        help="Base folder; videos are saved in a handle subfolder")
    parser.add_argument("--username", help="Load this user's existing Instaloader session")
    parser.add_argument("--session-file", type=Path, help="Optional custom session file")
    args = parser.parse_args()
    if not args.urls and not args.profile:
        parser.error("Provide at least one URL or --profile HANDLE")
    if args.session_file and not args.username:
        parser.error("--session-file requires --username")

    try:
        import instaloader
    except ImportError:
        print("Install the dependency: python -m pip install -r requirements.txt", file=sys.stderr)
        return 1

    loader = instaloader.Instaloader(max_connection_attempts=3, request_timeout=60)
    try:
        args.output.mkdir(parents=True, exist_ok=True)
        if args.username:
            loader.load_session_from_file(
                args.username,
                filename=str(args.session_file) if args.session_file else None,
            )
    except (OSError, instaloader.exceptions.InstaloaderException) as exc:
        print(f"Setup failed: {exc}", file=sys.stderr)
        return 1

    failed = False
    seen = set()

    def download_post(post, output, require_video=False):
        nonlocal failed
        shortcode = post.shortcode
        if shortcode in seen:
            return
        try:
            output = output / profile_handle(post.owner_username).lower()
            output.mkdir(parents=True, exist_ok=True)
            if post.typename == "GraphSidecar":
                videos = [(index, node.video_url) for index, node in
                          enumerate(post.get_sidecar_nodes(), start=1) if node.is_video]
            elif post.is_video:
                videos = [(1, post.video_url)]
            else:
                videos = []
            if not videos:
                if require_video:
                    print(f"{shortcode}: no videos found.", file=sys.stderr)
                    failed = True
                seen.add(shortcode)
                return
            for index, url in videos:
                if not url:
                    raise ValueError("Instagram did not return a video URL.")
                filename = output / f"{shortcode}_{index}.mp4"
                if filename.exists():
                    print(f"Already exists: {filename}")
                    continue
                loader.download_pic(str(filename.with_suffix("")), url, post.date_utc)
                print(f"Saved: {filename}")
            seen.add(shortcode)
        except (instaloader.exceptions.InstaloaderException, OSError, ValueError) as exc:
            print(f"{shortcode}: {exc}", file=sys.stderr)
            print("If Instagram requires login, use --username with a saved session.", file=sys.stderr)
            failed = True
    for shortcode in dict.fromkeys(args.urls):
        try:
            post = instaloader.Post.from_shortcode(loader.context, shortcode)
            download_post(post, args.output, require_video=True)
        except instaloader.exceptions.InstaloaderException as exc:
            print(f"{shortcode}: {exc}", file=sys.stderr)
            failed = True

    if args.profile:
        try:
            profile = instaloader.Profile.from_username(loader.context, args.profile)
            for label, fetch in (("posts", profile.get_posts), ("Reels", profile.get_reels)):
                print(f"Scanning @{args.profile} {label}...")
                try:
                    for post in fetch():
                        download_post(post, args.output)
                except instaloader.exceptions.InstaloaderException as exc:
                    print(f"Could not finish {label}: {exc}", file=sys.stderr)
                    failed = True
        except (instaloader.exceptions.InstaloaderException, OSError) as exc:
            print(f"@{args.profile}: {exc}", file=sys.stderr)
            failed = True
        if failed:
            print("Profile download incomplete. Try a saved login session with --username, "
                  "or retry later if rate limited. Existing files will be skipped.", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
