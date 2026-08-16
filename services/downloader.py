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
    target_mb=42.0,
    progress_callback=None
):
    """
    Compress a video to approximately target_mb.

    Designed for Telegram uploads.
    """

    if not os.path.isfile(input_file):
        raise FileNotFoundError(
            f"Input video not found: {input_file}"
        )

    output_file = os.path.join(
        TEMP_DIR,
        f"compressed_{uuid.uuid4().hex}.mp4"
    )

    original_size = os.path.getsize(input_file)

    original_mb = (
        original_size / (1024 * 1024)
    )

    print()
    print("=" * 70)
    print("FFMPEG COMPRESSION")
    print("=" * 70)

    print("Input:", input_file)
    print(
        "Original size:",
        f"{original_mb:.2f} MB"
    )
    print(
        "Target size:",
        f"{target_mb:.2f} MB"
    )

    # =====================================================
    # GET VIDEO INFORMATION
    # =====================================================

    probe_command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,duration",
        "-of",
        "json",
        input_file
    ]

    try:

        probe = subprocess.run(
            probe_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="replace",
            timeout=60
        )

        if probe.returncode != 0:
            raise RuntimeError(
                probe.stderr
            )

        import json

        probe_data = json.loads(
            probe.stdout
        )

        streams = probe_data.get(
            "streams",
            []
        )

        if not streams:
            raise RuntimeError(
                "FFprobe could not find a video stream."
            )

        video_stream = streams[0]

        width = int(
            video_stream.get(
                "width",
                1280
            )
        )

        height = int(
            video_stream.get(
                "height",
                720
            )
        )

        duration = float(
            video_stream.get(
                "duration",
                0
            )
            or 0
        )

    except Exception as error:

        print(
            "FFprobe error:",
            error
        )

        raise RuntimeError(
            f"Could not read video information: {error}"
        )

    if duration <= 0:

        # Try format-level duration
        probe_command = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            input_file
        ]

        probe = subprocess.run(
            probe_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="replace"
        )

        try:
            duration = float(
                probe.stdout.strip()
            )
        except Exception:
            duration = 0

    if duration <= 0:

        raise RuntimeError(
            "Could not determine video duration."
        )

    print(
        "Resolution:",
        f"{width}x{height}"
    )

    print(
        "Duration:",
        f"{duration:.2f} seconds"
    )

    # =====================================================
    # CALCULATE BITRATE
    # =====================================================

    target_bytes = (
        target_mb *
        1024 *
        1024
    )

    target_bits = (
        target_bytes * 8
    )

    # Reserve audio bitrate.
    audio_kbps = 64

    # Reserve container overhead.
    usable_bits = (
        target_bits * 0.90
    )

    total_kbps = (
        usable_bits /
        duration /
        1000
    )

    video_kbps = int(
        total_kbps - audio_kbps
    )

    # Prevent unusably low bitrate.
    video_kbps = max(
        video_kbps,
        150
    )

    print(
        "Calculated video bitrate:",
        f"{video_kbps} kbps"
    )

    # =====================================================
    # RESOLUTION CONTROL
    # =====================================================

    # Extremely large videos are unnecessarily expensive
    # to encode and may consume too much RAM/CPU.
    #
    # Keep 1080p videos at 1080p.
    # Reduce 1440p/4K videos.
    # For extremely low bitrates, reduce resolution.

    if width >= 3840:

        scale_filter = (
            "scale=-2:1080"
        )

    elif width >= 2560:

        scale_filter = (
            "scale=-2:1080"
        )

    elif video_kbps < 700 and height > 720:

        scale_filter = (
            "scale=-2:720"
        )

    elif video_kbps < 450 and height > 480:

        scale_filter = (
            "scale=-2:480"
        )

    elif video_kbps < 300 and height > 360:

        scale_filter = (
            "scale=-2:360"
        )

    else:

        scale_filter = (
            "scale='min(1920,iw)':-2"
        )

    print(
        "Scale filter:",
        scale_filter
    )

    # =====================================================
    # FFMPEG COMMAND
    # =====================================================

    command = [
        "ffmpeg",

        "-y",

        "-hide_banner",

        "-loglevel",
        "warning",

        "-i",
        input_file,

        # VIDEO
        "-vf",
        scale_filter,

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

        "-pix_fmt",
        "yuv420p",

        # AUDIO
        "-c:a",
        "aac",

        "-b:a",
        f"{audio_kbps}k",

        "-ac",
        "2",

        # MP4
        "-movflags",
        "+faststart",

        output_file
    ]

    print()
    print(
        "Running FFmpeg..."
    )

    print(
        "Command:",
        " ".join(command)
    )

    # =====================================================
    # RUN FFMPEG
    # =====================================================

    try:

        process = subprocess.Popen(

            command,

            stdout=subprocess.PIPE,

            stderr=subprocess.PIPE,

            text=True,

            errors="replace",

            bufsize=1
        )

        stdout, stderr = process.communicate()

    except Exception as error:

        print(
            "FFmpeg process error:",
            error
        )

        raise RuntimeError(
            f"Could not start FFmpeg: {error}"
        )

    # =====================================================
    # CHECK RESULT
    # =====================================================

    if process.returncode != 0:

        print()
        print("=" * 70)
        print("FFMPEG ERROR")
        print("=" * 70)

        print(stderr[-8000:])

        print("=" * 70)

        if os.path.exists(output_file):

            try:
                os.remove(
                    output_file
                )
            except Exception:
                pass

        raise RuntimeError(
            "FFmpeg compression failed.\n\n"
            + stderr[-4000:]
        )

    # =====================================================
    # VERIFY OUTPUT
    # =====================================================

    if not os.path.isfile(
        output_file
    ):

        raise RuntimeError(
            "FFmpeg finished but "
            "no output file was created."
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
    print("FFMPEG COMPRESSION COMPLETE")
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
                    "Compression complete: "
                    f"{compressed_mb:.2f} MB"
                )
        }
    )

    # =====================================================
    # IF STILL TOO LARGE
    # =====================================================

    if compressed_mb > 48:

        print(
            "Compressed file is still above "
            "Telegram safe limit."
        )

        # Remove first result.
        try:

            os.remove(
                output_file
            )

        except Exception:
            pass

        # Use stronger settings.
        output_file_2 = os.path.join(
            TEMP_DIR,
            f"compressed_strong_{uuid.uuid4().hex}.mp4"
        )

        stronger_kbps = max(
            120,
            int(
                video_kbps * 0.65
            )
        )

        print(
            "Retry bitrate:",
            f"{stronger_kbps} kbps"
        )

        command_2 = [

            "ffmpeg",

            "-y",

            "-hide_banner",

            "-loglevel",
            "warning",

            "-i",
            input_file,

            "-vf",
            "scale='min(1280,iw)':-2",

            "-c:v",
            "libx264",

            "-preset",
            "veryfast",

            "-b:v",
            f"{stronger_kbps}k",

            "-maxrate",
            f"{stronger_kbps}k",

            "-bufsize",
            f"{stronger_kbps * 2}k",

            "-pix_fmt",
            "yuv420p",

            "-c:a",
            "aac",

            "-b:a",
            "48k",

            "-ac",
            "2",

            "-movflags",
            "+faststart",

            output_file_2
        ]

        process_2 = subprocess.Popen(

            command_2,

            stdout=subprocess.PIPE,

            stderr=subprocess.PIPE,

            text=True,

            errors="replace"
        )

        stdout_2, stderr_2 = (
            process_2.communicate()
        )

        if process_2.returncode != 0:

            print(
                stderr_2[-8000:]
            )

            if os.path.exists(
                output_file_2
            ):

                try:
                    os.remove(
                        output_file_2
                    )
                except Exception:
                    pass

            raise RuntimeError(
                "FFmpeg second compression attempt failed.\n\n"
                + stderr_2[-4000:]
            )

        if not os.path.isfile(
            output_file_2
        ):

            raise RuntimeError(
                "Second FFmpeg compression "
                "did not create an output file."
            )

        compressed_size = os.path.getsize(
            output_file_2
        )

        compressed_mb = (
            compressed_size /
            (1024 * 1024)
        )

        output_file = output_file_2

        print(
            "Second compression:",
            f"{compressed_mb:.2f} MB"
        )

    # =====================================================
    # FINAL CHECK
    # =====================================================

    if compressed_mb > 48:

        try:

            os.remove(
                output_file
            )

        except Exception:
            pass

        raise RuntimeError(

            "Video is still too large after compression.\n\n"

            f"Final size: {compressed_mb:.2f} MB\n"

            "Please select a lower quality such as "
            "360p or 480p."
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