import os
import sys
import uuid
import glob
import json
import shutil
import subprocess
from pathlib import Path

import yt_dlp


# =========================================================
# CONFIGURATION
# =========================================================

TEMP_DIR = "temp"

os.makedirs(
    TEMP_DIR,
    exist_ok=True
)


# =========================================================
# QUALITY FORMATS
# =========================================================

QUALITY_FORMATS = {
    "144":
        "bestvideo[height<=144]+bestaudio/"
        "best[height<=144]/best",

    "240":
        "bestvideo[height<=240]+bestaudio/"
        "best[height<=240]/best",

    "360":
        "bestvideo[height<=360]+bestaudio/"
        "best[height<=360]/best",

    "480":
        "bestvideo[height<=480]+bestaudio/"
        "best[height<=480]/best",

    "540":
        "bestvideo[height<=540]+bestaudio/"
        "best[height<=540]/best",

    "720":
        "bestvideo[height<=720]+bestaudio/"
        "best[height<=720]/best",

    "1080":
        "bestvideo[height<=1080]+bestaudio/"
        "best[height<=1080]/best",

    "1440":
        "bestvideo[height<=1440]+bestaudio/"
        "best[height<=1440]/best",

    "2160":
        "bestvideo[height<=2160]+bestaudio/"
        "best[height<=2160]/best",

    "best":
        "bestvideo+bestaudio/best",
}


# =========================================================
# TELEGRAM SAFE SIZE
# =========================================================

MAX_UPLOAD_MB = 48.0

COMPRESSION_TARGET_MB = 42.0


# =========================================================
# VIDEO EXTENSIONS
# =========================================================

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".webm",
    ".mov",
    ".avi",
    ".m4v",
}


# =========================================================
# PROGRESS
# =========================================================

def safe_progress(
    progress_callback,
    data
):

    if progress_callback is None:
        return

    try:

        progress_callback(
            data
        )

    except Exception as error:

        print(
            "Progress callback error:",
            error
        )


# =========================================================
# FORMAT BYTES
# =========================================================

def format_bytes(
    value
):

    try:

        value = float(
            value
        )

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

            return (
                f"{value:.2f} {unit}"
            )

        value /= 1024

    return (
        f"{value:.2f} PB"
    )


# =========================================================
# FORMAT ETA
# =========================================================

def format_eta(
    seconds
):

    if seconds is None:
        return "--"

    try:

        seconds = int(
            float(seconds)
        )

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

    return (
        f"{seconds}s"
    )


# =========================================================
# CHECK PROGRAM
# =========================================================

def check_program(
    program
):

    path = shutil.which(
        program
    )

    if not path:

        raise RuntimeError(
            f"{program} is not installed "
            "or is not available in PATH."
        )

    return path


# =========================================================
# YOUTUBE OPTIONS
# =========================================================

def add_youtube_options(
    options
):

    # -----------------------------------------------------
    # DENO
    # -----------------------------------------------------

    deno_path = shutil.which(
        "deno"
    )

    if deno_path:

        print(
            "Deno found:",
            deno_path
        )

        # IMPORTANT:
        # Current yt-dlp expects:
        #
        # {
        #     "deno": {}
        # }

        options[
            "js_runtimes"
        ] = {
            "deno": {}
        }

        options[
            "remote_components"
        ] = [
            "ejs:npm"
        ]

    else:

        print(
            "WARNING: Deno not found."
        )

    # -----------------------------------------------------
    # COOKIES
    # -----------------------------------------------------

    cookies_file = os.getenv(
        "YOUTUBE_COOKIES_FILE",
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

            print(
                "YouTube cookies enabled."
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
# FACEBOOK OPTIONS
# =========================================================

def add_facebook_options(
    options
):

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

    if not cookies_file:
        return

    cookies_file = os.path.abspath(
        cookies_file
    )

    if os.path.isfile(
        cookies_file
    ):

        options[
            "cookiefile"
        ] = cookies_file


# =========================================================
# AVAILABLE QUALITIES
# =========================================================

def get_available_qualities(
    url,
    platform=None,
    progress_callback=None
):

    safe_progress(
        progress_callback,
        {
            "stage":
                "fetching",

            "percent":
                0,

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
        "yt-dlp:",
        yt_dlp.version.__version__
    )

    print("=" * 70)

    options = {

        "quiet":
            False,

        "no_warnings":
            False,

        "skip_download":
            True,

        "noplaylist":
            True,

        "socket_timeout":
            60,

        "retries":
            5,

        "fragment_retries":
            5,

    }

    # -----------------------------------------------------
    # PLATFORM OPTIONS
    # -----------------------------------------------------

    if platform == "youtube":

        add_youtube_options(
            options
        )

    elif platform == "facebook":

        add_facebook_options(
            options
        )

    # -----------------------------------------------------
    # EXTRACT
    # -----------------------------------------------------

    with yt_dlp.YoutubeDL(
        options
    ) as ydl:

        info = ydl.extract_info(
            url,
            download=False
        )

    if not info:

        raise RuntimeError(
            "yt-dlp returned no information."
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

    for requested in requested_heights:

        if any(
            actual >= requested
            for actual in heights
        ):

            available.append(
                str(requested)
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
        "Resolutions:",
        sorted(
            heights
        )
    )

    print(
        "Selectable:",
        available
    )

    print("=" * 70)

    safe_progress(
        progress_callback,
        {
            "stage":
                "fetching",

            "percent":
                100,

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
            "stage":
                "downloading",

            "percent":
                0,

            "downloaded":
                0,

            "total":
                0,

            "speed":
                0,

            "eta":
                None,

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

    print("=" * 70)

    last_percent = -1

    # -----------------------------------------------------
    # PROGRESS HOOK
    # -----------------------------------------------------

    def progress_hook(
        data
    ):

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

            rounded = int(
                percent
            )

            if rounded != last_percent:

                last_percent = rounded

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
                        "Preparing video..."
                }
            )

    # -----------------------------------------------------
    # OPTIONS
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # PLATFORM
    # -----------------------------------------------------

    if platform == "youtube":

        add_youtube_options(
            options
        )

    elif platform == "facebook":

        add_facebook_options(
            options
        )

    # -----------------------------------------------------
    # DOWNLOAD
    # -----------------------------------------------------

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

        prepared_filename = (
            ydl.prepare_filename(
                info
            )
        )

    # -----------------------------------------------------
    # FIND FILE
    # -----------------------------------------------------

    possible_files = [

        prepared_filename,

        os.path.splitext(
            prepared_filename
        )[0]
        + ".mp4",
    ]

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

        if os.path.getsize(
            path
        ) <= 0:
            continue

        final_file = path

        if path.lower().endswith(
            ".mp4"
        ):

            break

    if not final_file:

        raise FileNotFoundError(
            "yt-dlp finished but the "
            "downloaded video was not found."
        )

    file_size = os.path.getsize(
        final_file
    )

    print()
    print("=" * 70)
    print("DOWNLOAD COMPLETE")
    print("=" * 70)

    print(
        "File:",
        final_file
    )

    print(
        "Size:",
        format_bytes(
            file_size
        )
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
                "Download complete."
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
# FFMPEG COMPRESSION
# =========================================================

def compress_video(
    input_file,
    target_mb=42.0,
    progress_callback=None
):

    # -----------------------------------------------------
    # CHECK INPUT
    # -----------------------------------------------------

    if not os.path.isfile(
        input_file
    ):

        raise FileNotFoundError(
            f"Input video not found:\n"
            f"{input_file}"
        )

    # -----------------------------------------------------
    # CHECK FFMPEG
    # -----------------------------------------------------

    ffmpeg_path = shutil.which(
        "ffmpeg"
    )

    if not ffmpeg_path:

        raise RuntimeError(
            "FFmpeg is not installed "
            "or is not available in PATH."
        )

    ffprobe_path = shutil.which(
        "ffprobe"
    )

    if not ffprobe_path:

        raise RuntimeError(
            "FFprobe is not installed "
            "or is not available in PATH."
        )

    # -----------------------------------------------------
    # FILE SIZE
    # -----------------------------------------------------

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

    print()
    print("=" * 70)
    print("FFMPEG COMPRESSION STARTED")
    print("=" * 70)

    print(
        "FFmpeg:",
        ffmpeg_path
    )

    print(
        "FFprobe:",
        ffprobe_path
    )

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

    # -----------------------------------------------------
    # PROBE VIDEO
    # -----------------------------------------------------

    probe_command = [

        ffprobe_path,

        "-v",
        "error",

        "-select_streams",
        "v:0",

        "-show_entries",
        "stream=width,height",

        "-show_entries",
        "format=duration",

        "-of",
        "json",

        input_file,
    ]

    try:

        probe = subprocess.run(

            probe_command,

            stdout=subprocess.PIPE,

            stderr=subprocess.PIPE,

            text=True,

            errors="replace",

            timeout=120
        )

    except Exception as error:

        raise RuntimeError(
            f"FFprobe could not run:\n{error}"
        )

    if probe.returncode != 0:

        raise RuntimeError(

            "FFprobe failed:\n\n"
            +
            probe.stderr[-5000:]
        )

    try:

        data = json.loads(
            probe.stdout
        )

    except Exception as error:

        raise RuntimeError(
            "Could not parse FFprobe output:\n"
            f"{error}"
        )

    streams = data.get(
        "streams",
        []
    )

    if not streams:

        raise RuntimeError(
            "No video stream found."
        )

    stream = streams[0]

    width = int(
        stream.get(
            "width",
            1280
        )
    )

    height = int(
        stream.get(
            "height",
            720
        )
    )

    duration = float(
        data.get(
            "format",
            {}
        ).get(
            "duration",
            0
        )
        or 0
    )

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

    # -----------------------------------------------------
    # BITRATE
    # -----------------------------------------------------

    target_bytes = (
        target_mb *
        1024 *
        1024
    )

    target_bits = (
        target_bytes *
        8
    )

    # Reserve space for:
    #
    # audio
    # MP4 container
    # metadata
    #
    audio_kbps = 64

    usable_bits = (
        target_bits *
        0.88
    )

    total_kbps = (
        usable_bits /
        duration /
        1000
    )

    video_kbps = int(
        total_kbps -
        audio_kbps
    )

    video_kbps = max(
        video_kbps,
        180
    )

    # -----------------------------------------------------
    # SCALE
    # -----------------------------------------------------

    if width >= 3840:

        scale_filter = (
            "scale=-2:1080"
        )

    elif width >= 2560:

        scale_filter = (
            "scale=-2:1080"
        )

    elif video_kbps < 600 and height > 720:

        scale_filter = (
            "scale=-2:720"
        )

    elif video_kbps < 400 and height > 480:

        scale_filter = (
            "scale=-2:480"
        )

    elif video_kbps < 280 and height > 360:

        scale_filter = (
            "scale=-2:360"
        )

    else:

        scale_filter = (
            "scale='min(1920,iw)':-2"
        )

    print(
        "Video bitrate:",
        f"{video_kbps} kbps"
    )

    print(
        "Scale:",
        scale_filter
    )

    # -----------------------------------------------------
    # FFMPEG COMMAND
    # -----------------------------------------------------

    command = [

        ffmpeg_path,

        "-y",

        "-hide_banner",

        "-i",
        input_file,

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

        "-c:a",
        "aac",

        "-b:a",
        "64k",

        "-ac",
        "2",

        "-movflags",
        "+faststart",

        output_file,
    ]

    print()
    print(
        "Running FFmpeg..."
    )

    print(
        " ".join(
            command
        )
    )

    # -----------------------------------------------------
    # RUN FFMPEG
    # -----------------------------------------------------

    try:

        process = subprocess.Popen(

            command,

            stdout=subprocess.PIPE,

            stderr=subprocess.PIPE,

            text=True,

            errors="replace",

            bufsize=1
        )

    except Exception as error:

        raise RuntimeError(
            f"Could not start FFmpeg:\n"
            f"{error}"
        )

    stderr_lines = []

    # -----------------------------------------------------
    # READ OUTPUT
    # -----------------------------------------------------

    while True:

        line = process.stderr.readline()

        if not line:

            if process.poll() is not None:

                break

            continue

        line = line.strip()

        if line:

            stderr_lines.append(
                line
            )

            # Keep memory bounded.
            if len(
                stderr_lines
            ) > 300:

                stderr_lines.pop(
                    0
                )

        # -------------------------------------------------
        # PROGRESS
        # -------------------------------------------------

        if (
            "time=" in line
            and
            duration > 0
        ):

            try:

                time_part = (
                    line
                    .split(
                        "time="
                    )[1]
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

    return_code = (
        process.wait()
    )

    # -----------------------------------------------------
    # FFMPEG FAILURE
    # -----------------------------------------------------

    if return_code != 0:

        error_text = "\n".join(
            stderr_lines
        )

        print()
        print("=" * 70)
        print("FFMPEG FAILED")
        print("=" * 70)

        print(
            "Return code:",
            return_code
        )

        print(
            error_text
        )

        print("=" * 70)

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

            "FFmpeg compression failed.\n\n"
            +
            error_text[-5000:]
        )

    # -----------------------------------------------------
    # OUTPUT CHECK
    # -----------------------------------------------------

    if not os.path.isfile(
        output_file
    ):

        raise RuntimeError(
            "FFmpeg completed but "
            "the compressed file was not created."
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

    # -----------------------------------------------------
    # SECOND PASS
    # -----------------------------------------------------

    if compressed_mb > MAX_UPLOAD_MB:

        print(
            "First compression is still too large."
        )

        second_file = os.path.join(
            TEMP_DIR,
            f"compressed2_{uuid.uuid4().hex}.mp4"
        )

        stronger_bitrate = max(
            120,
            int(
                video_kbps * 0.60
            )
        )

        second_command = [

            ffmpeg_path,

            "-y",

            "-hide_banner",

            "-i",
            input_file,

            "-vf",
            "scale='min(1280,iw)':-2",

            "-c:v",
            "libx264",

            "-preset",
            "veryfast",

            "-b:v",
            f"{stronger_bitrate}k",

            "-maxrate",
            f"{stronger_bitrate}k",

            "-bufsize",
            f"{stronger_bitrate * 2}k",

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

            second_file,
        ]

        print(
            "Running second compression..."
        )

        process2 = subprocess.run(

            second_command,

            stdout=subprocess.PIPE,

            stderr=subprocess.PIPE,

            text=True,

            errors="replace"
        )

        if process2.returncode != 0:

            print(
                process2.stderr[-5000:]
            )

            if os.path.exists(
                second_file
            ):

                try:

                    os.remove(
                        second_file
                    )

                except Exception:
                    pass

            raise RuntimeError(

                "Second FFmpeg compression failed.\n\n"
                +
                process2.stderr[-5000:]
            )

        if not os.path.isfile(
            second_file
        ):

            raise RuntimeError(
                "Second compression did not "
                "create an output file."
            )

        second_size = os.path.getsize(
            second_file
        )

        second_mb = (
            second_size /
            (1024 * 1024)
        )

        if os.path.exists(
            output_file
        ):

            try:

                os.remove(
                    output_file
                )

            except Exception:
                pass

        output_file = second_file

        compressed_mb = second_mb

        print(
            "Second compression:",
            f"{compressed_mb:.2f} MB"
        )

    # -----------------------------------------------------
    # FINAL SIZE CHECK
    # -----------------------------------------------------

    if compressed_mb > MAX_UPLOAD_MB:

        try:

            os.remove(
                output_file
            )

        except Exception:
            pass

        raise RuntimeError(

            "Video could not be compressed "
            "below the Telegram safe limit.\n\n"

            f"Final size: "
            f"{compressed_mb:.2f} MB\n\n"

            "Please choose a lower quality, "
            "such as 360p or 480p."
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
                    "Compression complete: "
                    f"{compressed_mb:.2f} MB"
                )
        }
    )

    return output_file


# =========================================================
# DELETE FILE
# =========================================================

def delete_file(
    file_path
):

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
            "Cleanup error:",
            error
        )