import os
import sys
import uuid
import glob
import json
import subprocess
import threading
from pathlib import Path

import yt_dlp


# =========================================================
# CONFIG
# =========================================================

TEMP_DIR = "temp"

os.makedirs(TEMP_DIR, exist_ok=True)


QUALITY_FORMATS = {
    "144": "bestvideo[height<=144]+bestaudio/best[height<=144]/best",
    "240": "bestvideo[height<=240]+bestaudio/best[height<=240]/best",
    "360": "bestvideo[height<=360]+bestaudio/best[height<=360]/best",
    "480": "bestvideo[height<=480]+bestaudio/best[height<=480]/best",
    "540": "bestvideo[height<=540]+bestaudio/best[height<=540]/best",
    "720": "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
    "1080": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
    "1440": "bestvideo[height<=1440]+bestaudio/best[height<=1440]/best",
    "2160": "bestvideo[height<=2160]+bestaudio/best[height<=2160]/best",
    "best": "bestvideo+bestaudio/best",
}


# =========================================================
# PROGRESS HELPER
# =========================================================

def safe_progress(progress_callback, data):
    """
    Progress callback must NEVER break yt-dlp/FFmpeg.
    """

    if progress_callback is None:
        return

    try:
        progress_callback(data)
    except Exception as error:
        print(
            "Progress callback error:",
            error
        )


# =========================================================
# HUMAN SIZE
# =========================================================

def format_bytes(value):

    try:
        value = float(value)
    except Exception:
        return "0 B"

    units = [
        "B",
        "KB",
        "MB",
        "GB",
    ]

    for unit in units:

        if value < 1024:

            return f"{value:.2f} {unit}"

        value /= 1024

    return f"{value:.2f} TB"


# =========================================================
# FORMAT ETA
# =========================================================

def format_eta(seconds):

    if seconds is None:
        return "--"

    try:
        seconds = int(float(seconds))
    except Exception:
        return "--"

    if seconds < 0:
        return "--"

    minutes, seconds = divmod(
        seconds,
        60
    )

    hours, minutes = divmod(
        minutes,
        60
    )

    if hours:
        return (
            f"{hours}h "
            f"{minutes}m "
            f"{seconds}s"
        )

    if minutes:
        return (
            f"{minutes}m "
            f"{seconds}s"
        )

    return f"{seconds}s"


# =========================================================
# GET AVAILABLE QUALITIES
# =========================================================

def get_available_qualities(
    url,
    platform=None,
    progress_callback=None
):

    safe_progress(
        progress_callback,
        {
            "stage": "fetching",
            "percent": 0,
            "message": "Fetching video information..."
        }
    )

    print()
    print("=" * 60)
    print("FETCHING VIDEO INFORMATION")
    print("=" * 60)

    options = {

        "quiet": True,

        "no_warnings": True,

        "skip_download": True,

        "noplaylist": True,

        "socket_timeout": 60,

    }

    if platform == "facebook":

        options[
            "http_headers"
        ] = {

            "User-Agent":
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/151.0.0.0 "
                "Safari/537.36",

            "Referer":
                "https://www.facebook.com/",
        }

    with yt_dlp.YoutubeDL(
        options
    ) as ydl:

        info = ydl.extract_info(
            url,
            download=False
        )

    formats = info.get(
        "formats",
        []
    )

    heights = set()

    for fmt in formats:

        height = fmt.get(
            "height"
        )

        if not height:
            continue

        try:
            height = int(
                height
            )
        except Exception:
            continue

        if height > 0:

            heights.add(
                height
            )

    available = []

    requested_heights = [
        144,
        240,
        360,
        480,
        540,
        720,
        1080,
        1440,
        2160,
    ]

    for height in requested_heights:

        if any(
            available_height >= height
            for available_height in heights
        ):

            available.append(
                str(height)
            )

    if formats:

        available.append(
            "best"
        )

    available = list(
        dict.fromkeys(
            available
        )
    )

    safe_progress(
        progress_callback,
        {
            "stage": "fetching",
            "percent": 100,
            "message": "Video information received."
        }
    )

    title = info.get(
        "title",
        "Video"
    )

    print(
        "Title:",
        title
    )

    print(
        "Available qualities:",
        available
    )

    print("=" * 60)

    return {
        "title": title,
        "qualities": available,
    }


# =========================================================
# YT-DLP DOWNLOAD
# =========================================================

def download_media(
    url,
    quality="best",
    platform=None,
    progress_callback=None
):

    safe_progress(
        progress_callback,
        {
            "stage": "downloading",
            "percent": 0,
            "downloaded": 0,
            "total": 0,
            "speed": 0,
            "eta": None,
            "message": "Starting download..."
        }
    )

    unique_id = uuid.uuid4().hex

    output_template = os.path.join(
        TEMP_DIR,
        f"{unique_id}.%(ext)s"
    )

    selected_format = QUALITY_FORMATS.get(
        str(quality),
        QUALITY_FORMATS["best"]
    )

    print()
    print("=" * 60)
    print("DOWNLOAD STARTED")
    print("=" * 60)

    print(
        "Platform:",
        platform
    )

    print(
        "Quality:",
        quality
    )

    print(
        "Format:",
        selected_format
    )

    print(
        "Python:",
        sys.executable
    )

    print("=" * 60)

    last_percent = -1

    def hook(data):

        nonlocal last_percent

        status = data.get(
            "status"
        )

        if status == "downloading":

            downloaded = data.get(
                "downloaded_bytes",
                0
            )

            total = (
                data.get(
                    "total_bytes"
                )
                or
                data.get(
                    "total_bytes_estimate"
                )
                or
                0
            )

            if total:

                percent = (
                    downloaded /
                    total
                ) * 100

            else:

                percent = 0

            speed = data.get(
                "speed",
                0
            )

            eta = data.get(
                "eta"
            )

            # Prevent excessive Telegram edits
            rounded_percent = int(
                percent
            )

            if (
                rounded_percent !=
                last_percent
            ):

                last_percent = (
                    rounded_percent
                )

                safe_progress(
                    progress_callback,
                    {
                        "stage":
                            "downloading",

                        "percent":
                            min(
                                percent,
                                100
                            ),

                        "downloaded":
                            downloaded,

                        "total":
                            total,

                        "speed":
                            speed,

                        "eta":
                            eta,

                        "message":
                            "Downloading..."
                    }
                )

        elif status == "finished":

            safe_progress(
                progress_callback,
                {
                    "stage":
                        "converting",

                    "percent":
                        0,

                    "message":
                        "Download complete. Preparing video..."
                }
            )

    options = {

        "format":
            selected_format,

        "outtmpl":
            output_template,

        "merge_output_format":
            "mp4",

        "noplaylist":
            True,

        "quiet":
            False,

        "no_warnings":
            False,

        "restrictfilenames":
            True,

        "windowsfilenames":
            True,

        "continuedl":
            True,

        "retries":
            5,

        "fragment_retries":
            5,

        "socket_timeout":
            60,

        "concurrent_fragment_downloads":
            4,

        "progress_hooks":
            [hook],

    }

    if platform == "facebook":

        options[
            "http_headers"
        ] = {

            "User-Agent":
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/151.0.0.0 "
                "Safari/537.36",

            "Referer":
                "https://www.facebook.com/",
        }

        cookies_file = os.getenv(
            "FACEBOOK_COOKIES_FILE",
            ""
        ).strip()

        if cookies_file:

            cookies_file = os.path.abspath(
                cookies_file
            )

            if os.path.isfile(
                cookies_file
            ):

                options[
                    "cookiefile"
                ] = cookies_file

    with yt_dlp.YoutubeDL(
        options
    ) as ydl:

        info = ydl.extract_info(
            url,
            download=True
        )

    title = info.get(
        "title",
        "Downloaded Video"
    )

    # -----------------------------------------------------
    # FIND FINAL FILE
    # -----------------------------------------------------

    possible_files = []

    try:

        prepared = ydl.prepare_filename(
            info
        )

        possible_files.append(
            prepared
        )

        possible_files.append(
            os.path.splitext(
                prepared
            )[0]
            + ".mp4"
        )

    except Exception:
        pass

    possible_files.extend(
        glob.glob(
            os.path.join(
                TEMP_DIR,
                f"{unique_id}.*"
            )
        )
    )

    final_file = None

    for file_path in possible_files:

        if not os.path.isfile(
            file_path
        ):
            continue

        if file_path.endswith(
            ".part"
        ):
            continue

        if file_path.endswith(
            ".ytdl"
        ):
            continue

        if os.path.getsize(
            file_path
        ) <= 0:
            continue

        final_file = file_path

        if file_path.lower().endswith(
            ".mp4"
        ):
            break

    if not final_file:

        raise FileNotFoundError(
            "yt-dlp finished but the "
            "final downloaded file was not found."
        )

    safe_progress(
        progress_callback,
        {
            "stage":
                "converting",

            "percent":
                100,

            "message":
                "Video conversion complete."
        }
    )

    print()
    print(
        "Downloaded:",
        final_file
    )

    print(
        "Size:",
        format_bytes(
            os.path.getsize(
                final_file
            )
        )
    )

    return {

        "file":
            final_file,

        "title":
            title,

        "ext":
            os.path.splitext(
                final_file
            )[1],

        "quality":
            quality,

        "platform":
            platform,
    }


# =========================================================
# FFMPEG COMPRESSION
# =========================================================

def compress_video(
    input_file,
    target_mb=47.0,
    progress_callback=None
):

    if not os.path.isfile(
        input_file
    ):

        raise FileNotFoundError(
            input_file
        )

    original_size = os.path.getsize(
        input_file
    )

    original_mb = (
        original_size /
        (1024 * 1024)
    )

    output_file = os.path.join(
        TEMP_DIR,
        f"compressed_{uuid.uuid4().hex}.mp4"
    )

    safe_progress(
        progress_callback,
        {
            "stage":
                "compressing",

            "percent":
                0,

            "message":
                f"Compressing {original_mb:.2f} MB..."
        }
    )

    # -----------------------------------------------------
    # GET DURATION
    # -----------------------------------------------------

    duration = 0

    probe_command = [

        "ffprobe",

        "-v",
        "error",

        "-show_entries",
        "format=duration",

        "-of",
        "default=noprint_wrappers=1:nokey=1",

        input_file,
    ]

    try:

        probe = subprocess.run(

            probe_command,

            capture_output=True,

            text=True,

            errors="replace"
        )

        duration = float(
            probe.stdout.strip()
        )

    except Exception:

        duration = 0

    # -----------------------------------------------------
    # TARGET BITRATE
    # -----------------------------------------------------

    if duration > 0:

        target_bits = (
            target_mb
            *
            1024
            *
            1024
            *
            8
        )

        # Reserve audio bitrate
        audio_bitrate = 96000

        video_bitrate = (
            target_bits /
            duration
        ) - audio_bitrate

        video_bitrate = max(
            video_bitrate,
            150000
        )

        video_kbps = int(
            video_bitrate / 1000
        )

    else:

        video_kbps = 1000

    # -----------------------------------------------------
    # FFMPEG
    # -----------------------------------------------------

    command = [

        "ffmpeg",

        "-y",

        "-i",
        input_file,

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-b:v",
        f"{video_kbps}k",

        "-maxrate",
        f"{video_kbps}k",

        "-bufsize",
        f"{video_kbps * 2}k",

        "-c:a",
        "aac",

        "-b:a",
        "96k",

        "-movflags",
        "+faststart",

        output_file,
    ]

    process = subprocess.Popen(

        command,

        stdout=subprocess.DEVNULL,

        stderr=subprocess.PIPE,

        text=True,

        errors="replace",

        bufsize=1
    )

    current_percent = 0

    while True:

        line = process.stderr.readline()

        if not line:

            if process.poll() is not None:
                break

            continue

        line = line.strip()

        # -------------------------------------------------
        # Parse FFmpeg time
        # -------------------------------------------------

        if "time=" in line and duration > 0:

            try:

                time_part = line.split(
                    "time="
                )[1].split()[0]

                hours, minutes, seconds = (
                    time_part.split(":")
                )

                elapsed = (
                    float(hours) * 3600
                    +
                    float(minutes) * 60
                    +
                    float(seconds)
                )

                current_percent = min(
                    (
                        elapsed /
                        duration
                    ) * 100,
                    100
                )

                safe_progress(
                    progress_callback,
                    {
                        "stage":
                            "compressing",

                        "percent":
                            current_percent,

                        "message":
                            "Compressing video..."
                    }
                )

            except Exception:
                pass

    return_code = process.wait()

    if return_code != 0:

        if os.path.exists(
            output_file
        ):

            os.remove(
                output_file
            )

        raise RuntimeError(
            "FFmpeg compression failed."
        )

    if not os.path.isfile(
        output_file
    ):

        raise RuntimeError(
            "Compressed video was not created."
        )

    compressed_size = os.path.getsize(
        output_file
    )

    compressed_mb = (
        compressed_size /
        (1024 * 1024)
    )

    safe_progress(
        progress_callback,
        {
            "stage":
                "compressing",

            "percent":
                100,

            "message":
                (
                    f"Compression complete: "
                    f"{compressed_mb:.2f} MB"
                )
        }
    )

    print(
        "Original size:",
        f"{original_mb:.2f} MB"
    )

    print(
        "Compressed size:",
        f"{compressed_mb:.2f} MB"
    )

    return output_file


# =========================================================
# DELETE FILE
# =========================================================

def delete_file(file_path):

    try:

        if file_path and os.path.exists(
            file_path
        ):

            os.remove(
                file_path
            )

            print(
                "Deleted:",
                file_path
            )

    except Exception as error:

        print(
            "Delete error:",
            error
        )