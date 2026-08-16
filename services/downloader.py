import os
import sys
import uuid
import glob
import subprocess

import yt_dlp


# =========================================================
# CONFIGURATION
# =========================================================

TEMP_DIR = "temp"

os.makedirs(TEMP_DIR, exist_ok=True)


# =========================================================
# QUALITY FORMATS
# =========================================================

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
# PROGRESS CALLBACK
# =========================================================

def safe_progress(progress_callback, data):

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
# FORMAT BYTES
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
        "TB",
    ]

    for unit in units:

        if value < 1024:
            return f"{value:.2f} {unit}"

        value /= 1024

    return f"{value:.2f} PB"


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

    hours, remainder = divmod(
        seconds,
        3600
    )

    minutes, seconds = divmod(
        remainder,
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
# YOUTUBE COOKIES
# =========================================================

def add_youtube_options(options):

    """
    Add YouTube cookie file if configured.

    Railway environment variable:

        YOUTUBE_COOKIES_FILE=/app/cookies/youtube.txt

    Never commit the cookie file to GitHub.
    """

    cookies_file = os.getenv(
        "YOUTUBE_COOKIES_FILE",
        ""
    ).strip()

    if not cookies_file:

        print(
            "YouTube cookies: not configured"
        )

        return

    cookies_file = os.path.abspath(
        cookies_file
    )

    if os.path.isfile(
        cookies_file
    ):

        options["cookiefile"] = (
            cookies_file
        )

        print(
            "YouTube cookies: enabled"
        )

    else:

        print(
            "WARNING: YouTube cookie file "
            "does not exist:"
        )

        print(
            cookies_file
        )


# =========================================================
# COMMON YOUTUBE OPTIONS
# =========================================================

def add_common_youtube_options(options):

    """
    Current yt-dlp YouTube configuration.

    IMPORTANT:
    js_runtimes must be a dictionary whose values
    are dictionaries.
    """

    # -----------------------------------------------------
    # DENO
    # -----------------------------------------------------

    options["js_runtimes"] = {
        "deno": {}
    }

    # -----------------------------------------------------
    # EJS
    # -----------------------------------------------------

    options["remote_components"] = [
        "ejs:npm"
    ]

    # -----------------------------------------------------
    # YOUTUBE COOKIES
    # -----------------------------------------------------

    add_youtube_options(
        options
    )


# =========================================================
# FACEBOOK OPTIONS
# =========================================================

def add_facebook_options(options):

    options["http_headers"] = {

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

    if not cookies_file:
        return

    cookies_file = os.path.abspath(
        cookies_file
    )

    if os.path.isfile(
        cookies_file
    ):

        options["cookiefile"] = (
            cookies_file
        )


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
            "message":
                "Fetching video information..."
        }
    )

    print()
    print("=" * 70)
    print("FETCHING VIDEO INFORMATION")
    print("=" * 70)

    print(
        "Platform:",
        platform
    )

    print(
        "URL:",
        url
    )

    print(
        "yt-dlp version:",
        yt_dlp.version.__version__
    )

    print("=" * 70)

    options = {

        "quiet": False,

        "no_warnings": False,

        "skip_download": True,

        "noplaylist": True,

        "socket_timeout": 60,

        "retries": 5,

        "fragment_retries": 5,

    }

    # =====================================================
    # YOUTUBE
    # =====================================================

    if platform == "youtube":

        add_common_youtube_options(
            options
        )

    # =====================================================
    # FACEBOOK
    # =====================================================

    elif platform == "facebook":

        add_facebook_options(
            options
        )

    # =====================================================
    # EXTRACT
    # =====================================================

    with yt_dlp.YoutubeDL(
        options
    ) as ydl:

        info = ydl.extract_info(
            url,
            download=False
        )

    if not info:

        raise RuntimeError(
            "yt-dlp returned no video information."
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

    available = []

    for height in requested_heights:

        # If there is a format at or above
        # requested resolution, make it available.
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

    title = info.get(
        "title",
        "Video"
    )

    duration = info.get(
        "duration"
    )

    print()
    print("=" * 70)
    print("VIDEO INFORMATION")
    print("=" * 70)

    print(
        "Title:",
        title
    )

    print(
        "Duration:",
        duration
    )

    print(
        "Available resolutions:",
        sorted(
            heights
        )
    )

    print(
        "Selectable qualities:",
        available
    )

    print("=" * 70)

    safe_progress(
        progress_callback,
        {
            "stage": "fetching",
            "percent": 100,
            "message":
                "Video information received."
        }
    )

    return {

        "title":
            title,

        "qualities":
            available,

        "duration":
            duration,

        "formats":
            formats,
    }


# =========================================================
# DOWNLOAD MEDIA
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
            "message":
                "Starting download..."
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
    print("=" * 70)
    print("DOWNLOAD STARTED")
    print("=" * 70)

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
        "URL:",
        url
    )

    print(
        "yt-dlp:",
        yt_dlp.version.__version__
    )

    print("=" * 70)

    last_percent = -1

    def progress_hook(data):

        nonlocal last_percent

        status = data.get(
            "status"
        )

        # =================================================
        # DOWNLOADING
        # =================================================

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

            rounded_percent = int(
                percent
            )

            if rounded_percent != last_percent:

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

        # =================================================
        # DOWNLOAD FINISHED
        # =================================================

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

    # =====================================================
    # YT-DLP OPTIONS
    # =====================================================

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
            [
                progress_hook
            ],

    }

    # =====================================================
    # YOUTUBE
    # =====================================================

    if platform == "youtube":

        add_common_youtube_options(
            options
        )

    # =====================================================
    # FACEBOOK
    # =====================================================

    elif platform == "facebook":

        add_facebook_options(
            options
        )

    # =====================================================
    # DOWNLOAD
    # =====================================================

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

        # Prepare filename before
        # YoutubeDL context closes.
        prepared_filename = (
            ydl.prepare_filename(
                info
            )
        )

    # =====================================================
    # FIND OUTPUT FILE
    # =====================================================

    possible_files = []

    possible_files.append(
        prepared_filename
    )

    possible_files.append(
        os.path.splitext(
            prepared_filename
        )[0]
        + ".mp4"
    )

    possible_files.extend(
        glob.glob(
            os.path.join(
                TEMP_DIR,
                f"{unique_id}.*"
            )
        )
    )

    final_file = None

    for path in possible_files:

        if not os.path.isfile(
            path
        ):
            continue

        if path.endswith(
            ".part"
        ):
            continue

        if path.endswith(
            ".ytdl"
        ):
            continue

        try:

            size = os.path.getsize(
                path
            )

        except Exception:

            continue

        if size <= 0:
            continue

        if path.lower().endswith(
            ".mp4"
        ):

            final_file = path

            break

        if final_file is None:

            final_file = path

    if not final_file:

        raise FileNotFoundError(
            "yt-dlp finished but "
            "the final video file was not found."
        )

    final_size = os.path.getsize(
        final_file
    )

    final_mb = (
        final_size /
        (1024 * 1024)
    )

    print()
    print("=" * 70)
    print("DOWNLOAD COMPLETE")
    print("=" * 70)

    print(
        "Title:",
        title
    )

    print(
        "File:",
        final_file
    )

    print(
        "Size:",
        f"{final_mb:.2f} MB"
    )

    print("=" * 70)

    safe_progress(
        progress_callback,
        {
            "stage":
                "converting",

            "percent":
                100,

            "message":
                "Video preparation complete."
        }
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
# COMPRESS VIDEO
# =========================================================

def compress_video(
    input_file,
    target_mb=44.0,
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

    print()
    print("=" * 70)
    print("COMPRESSION STARTED")
    print("=" * 70)

    print(
        "Input:",
        input_file
    )

    print(
        "Original:",
        f"{original_mb:.2f} MB"
    )

    print(
        "Target:",
        f"{target_mb:.2f} MB"
    )

    # =====================================================
    # GET DURATION
    # =====================================================

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

    except Exception as error:

        print(
            "ffprobe error:",
            error
        )

        duration = 0

    if duration <= 0:

        raise RuntimeError(
            "Could not determine video duration."
        )

    print(
        "Duration:",
        f"{duration:.2f} seconds"
    )

    # =====================================================
    # BITRATE CALCULATION
    # =====================================================

    target_bytes = (
        target_mb *
        1024 *
        1024
    )

    target_bits = (
        target_bytes *
        8
    )

    # Reserve some room for MP4 container overhead.
    usable_bits = (
        target_bits *
        0.93
    )

    # Audio = 64 kbps.
    audio_bitrate = 64000

    total_bitrate = (
        usable_bits /
        duration
    )

    video_bitrate = (
        total_bitrate -
        audio_bitrate
    )

    # Avoid invalid/very tiny bitrate.
    video_bitrate = max(
        video_bitrate,
        100000
    )

    video_kbps = int(
        video_bitrate /
        1000
    )

    print(
        "Video bitrate:",
        f"{video_kbps} kbps"
    )

    # =====================================================
    # FFMPEG
    # =====================================================

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
        "64k",

        "-movflags",
        "+faststart",

        output_file,
    ]

    print(
        "Running FFmpeg..."
    )

    process = subprocess.Popen(

        command,

        stdout=subprocess.DEVNULL,

        stderr=subprocess.PIPE,

        text=True,

        errors="replace",

        bufsize=1
    )

    # =====================================================
    # READ FFMPEG PROGRESS
    # =====================================================

    while True:

        line = process.stderr.readline()

        if not line:

            if process.poll() is not None:

                break

            continue

        line = line.strip()

        if "time=" not in line:

            continue

        try:

            time_part = (
                line
                .split("time=")[1]
                .split()[0]
            )

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

            percent = min(

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
                        percent,

                    "message":
                        "Compressing video..."
                }
            )

        except Exception:
            pass

    return_code = process.wait()

    # =====================================================
    # CHECK FFMPEG
    # =====================================================

    if return_code != 0:

        if os.path.exists(
            output_file
        ):

            try:
                os.remove(
                    output_file
                )
            except Exception:
                pass

        raise RuntimeError(
            "FFmpeg compression failed."
        )

    if not os.path.isfile(
        output_file
    ):

        raise RuntimeError(
            "FFmpeg completed but "
            "compressed video was not created."
        )

    compressed_size = os.path.getsize(
        output_file
    )

    compressed_mb = (
        compressed_size /
        (1024 * 1024)
    )

    print()
    print("=" * 70)
    print("COMPRESSION COMPLETE")
    print("=" * 70)

    print(
        "Original:",
        f"{original_mb:.2f} MB"
    )

    print(
        "Compressed:",
        f"{compressed_mb:.2f} MB"
    )

    print("=" * 70)

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

    return output_file


# =========================================================
# DELETE FILE
# =========================================================

def delete_file(file_path):

    if not file_path:
        return

    try:

        if os.path.exists(
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
            "Could not delete file:",
            file_path
        )

        print(
            "Error:",
            error
        )