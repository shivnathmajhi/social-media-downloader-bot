import os
import asyncio
from pathlib import Path

from dotenv import load_dotenv

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from services.downloader import (
    download_media,
    get_available_qualities,
    compress_video,
)


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError(
        "BOT_TOKEN not found.\n"
        "Create a .env file and add:\n\n"
        "BOT_TOKEN=YOUR_BOT_TOKEN"
    )


# =========================================================
# CONSTANTS
# =========================================================

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".webm",
    ".mov",
    ".avi",
    ".m4v",
}

# Telegram safety limit for this bot.
# We deliberately use 48 MB rather than pushing the limit.
MAX_UPLOAD_MB = 48.0

# Compression target.
# 44 MB gives us a safety margin.
COMPRESSION_TARGET_MB = 44.0


# =========================================================
# PLATFORM NAMES
# =========================================================

PLATFORM_NAMES = {
    "youtube": "▶️ YouTube",
    "tiktok": "🎵 TikTok",
    "facebook": "📘 Facebook",
    "x": "𝕏 X / Twitter",
    "whatsapp": "💬 WhatsApp",
}


# =========================================================
# QUALITY DISPLAY NAMES
# =========================================================

QUALITY_NAMES = {
    "144": "📱 144p",
    "240": "📱 240p",
    "360": "📱 360p",
    "480": "📺 480p",
    "540": "📺 540p",
    "720": "🎬 720p HD",
    "1080": "🔥 1080p Full HD",
    "1440": "💎 1440p 2K",
    "2160": "💎 2160p 4K",
    "best": "⭐ Best Available",
}


# =========================================================
# MAIN MENU
# =========================================================

def main_menu_keyboard():

    keyboard = [
        [
            InlineKeyboardButton(
                "▶️ YouTube",
                callback_data="youtube"
            )
        ],
        [
            InlineKeyboardButton(
                "🎵 TikTok",
                callback_data="tiktok"
            )
        ],
        [
            InlineKeyboardButton(
                "📘 Facebook",
                callback_data="facebook"
            )
        ],
        [
            InlineKeyboardButton(
                "𝕏 X / Twitter",
                callback_data="x"
            )
        ],
        [
            InlineKeyboardButton(
                "💬 WhatsApp",
                callback_data="whatsapp"
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# BACK BUTTON
# =========================================================

def back_button():

    keyboard = [
        [
            InlineKeyboardButton(
                "🔙 Back to Menu",
                callback_data="back_to_menu"
            )
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# QUALITY KEYBOARD
# =========================================================

def quality_keyboard(qualities):

    keyboard = []

    numeric = []

    for quality in qualities:

        if quality == "best":
            continue

        try:
            numeric.append(
                str(quality)
            )
        except Exception:
            pass

    numeric = list(
        dict.fromkeys(numeric)
    )

    try:
        numeric.sort(
            key=lambda x: int(x)
        )
    except Exception:
        pass

    row = []

    for quality in numeric:

        label = QUALITY_NAMES.get(
            quality,
            f"🎬 {quality}p"
        )

        row.append(
            InlineKeyboardButton(
                label,
                callback_data=f"quality_{quality}"
            )
        )

        if len(row) == 2:

            keyboard.append(row)

            row = []

    if row:
        keyboard.append(row)

    if "best" in qualities:

        keyboard.append(
            [
                InlineKeyboardButton(
                    "⭐ Best Available",
                    callback_data="quality_best"
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "🔙 Back to Menu",
                callback_data="back_to_menu"
            )
        ]
    )

    return InlineKeyboardMarkup(
        keyboard
    )


# =========================================================
# /START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()

    await update.message.reply_text(

        "👋 Welcome to Social Media Downloader!\n\n"
        "Choose the platform:",

        reply_markup=main_menu_keyboard()
    )


# =========================================================
# BACK TO MENU
# =========================================================

async def back_to_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    context.user_data.clear()

    await query.edit_message_text(

        "👋 Welcome to Social Media Downloader!\n\n"
        "Choose the platform:",

        reply_markup=main_menu_keyboard()
    )


# =========================================================
# PLATFORM SELECTED
# =========================================================

async def platform_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    platform = query.data

    context.user_data.clear()

    context.user_data["platform"] = platform

    platform_name = PLATFORM_NAMES.get(
        platform,
        platform
    )

    if platform in {
        "youtube",
        "tiktok",
        "facebook",
    }:

        await query.edit_message_text(

            f"✅ {platform_name} selected!\n\n"
            "🔗 Send me the video URL.",

            reply_markup=back_button()
        )

        return

    await query.edit_message_text(

        f"✅ Selected: {platform_name}\n\n"
        "⚠️ This platform is not enabled yet.\n\n"
        "It will be added in the next step.",

        reply_markup=back_button()
    )


# =========================================================
# HANDLE URL
# =========================================================

async def handle_url(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    url = update.message.text.strip()

    platform = context.user_data.get(
        "platform"
    )

    if not platform:

        await update.message.reply_text(

            "⚠️ Please select a platform first.",

            reply_markup=main_menu_keyboard()
        )

        return

    if not (
        url.startswith("http://")
        or
        url.startswith("https://")
    ):

        await update.message.reply_text(

            "❌ Invalid URL.\n\n"
            "Please send a valid http/https URL.",

            reply_markup=back_button()
        )

        return

    if platform not in {
        "youtube",
        "tiktok",
        "facebook",
    }:

        await update.message.reply_text(

            "⚠️ This platform is not enabled yet.",

            reply_markup=main_menu_keyboard()
        )

        return

    context.user_data["url"] = url

    status_message = await update.message.reply_text(

        "🔎 Fetching available qualities...\n\n"
        "Please wait..."
    )

    try:

        info = await asyncio.to_thread(

            get_available_qualities,

            url,

            platform
        )

        qualities = info.get(
            "qualities",
            []
        )

        title = info.get(
            "title",
            "Video"
        )

        if not qualities:

            raise RuntimeError(
                "No downloadable video qualities were found."
            )

        context.user_data["qualities"] = qualities

        context.user_data["title"] = title

        await status_message.edit_text(

            "🎬 Choose video quality:\n\n"
            f"🎥 {title}\n\n"
            "Only qualities actually available "
            "for this video are shown.",

            reply_markup=quality_keyboard(
                qualities
            )
        )

    except Exception as error:

        print()
        print("=" * 60)
        print("QUALITY FETCH ERROR")
        print("=" * 60)
        print(str(error))
        print("=" * 60)

        await status_message.edit_text(

            "❌ Could not fetch video qualities.\n\n"
            f"{str(error)}",

            reply_markup=main_menu_keyboard()
        )


# =========================================================
# QUALITY SELECTED
# =========================================================

async def quality_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    quality = query.data.replace(
        "quality_",
        "",
        1
    )

    url = context.user_data.get(
        "url"
    )

    platform = context.user_data.get(
        "platform"
    )

    available_qualities = context.user_data.get(
        "qualities",
        []
    )

    if not url:

        await query.edit_message_text(

            "❌ URL expired.\n\n"
            "Please start again.",

            reply_markup=main_menu_keyboard()
        )

        return

    if platform not in {
        "youtube",
        "tiktok",
        "facebook",
    }:

        await query.edit_message_text(

            "❌ Platform not available.",

            reply_markup=main_menu_keyboard()
        )

        return

    if quality != "best":

        if quality not in available_qualities:

            await query.edit_message_text(

                "❌ That quality is not available "
                "for this video.\n\n"
                "Please select another quality.",

                reply_markup=quality_keyboard(
                    available_qualities
                )
            )

            return

    quality_name = QUALITY_NAMES.get(
        quality,
        f"{quality}p"
    )

    platform_name = PLATFORM_NAMES.get(
        platform,
        platform
    )

    await query.edit_message_text(

        "⏳ Starting download...\n\n"
        f"📱 {platform_name}\n"
        f"🎬 {quality_name}\n\n"
        "Please wait..."
    )

    file_path = None
    compressed_path = None

    try:

        # =================================================
        # DOWNLOAD
        # =================================================

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
            "URL:",
            url
        )

        print("=" * 60)

        result = await asyncio.to_thread(

            download_media,

            url,

            quality,

            platform
        )

        if not result:

            raise RuntimeError(
                "Downloader returned no result."
            )

        file_path = result.get(
            "file"
        )

        title = result.get(
            "title",
            "Downloaded Video"
        )

        if not file_path:

            raise RuntimeError(
                "No downloaded file path returned."
            )

        if not os.path.exists(
            file_path
        ):

            raise FileNotFoundError(
                f"Downloaded file does not exist:\n"
                f"{file_path}"
            )

        # =================================================
        # ORIGINAL SIZE
        # =================================================

        file_size = os.path.getsize(
            file_path
        )

        file_size_mb = (
            file_size /
            (1024 * 1024)
        )

        extension = Path(
            file_path
        ).suffix.lower()

        print()
        print("=" * 60)
        print("DOWNLOAD COMPLETE")
        print("=" * 60)

        print(
            "File:",
            file_path
        )

        print(
            "Original size:",
            f"{file_size_mb:.2f} MB"
        )

        print("=" * 60)

        # =================================================
        # AUTOMATIC COMPRESSION
        # =================================================

        if (
            extension in VIDEO_EXTENSIONS
            and
            file_size_mb > MAX_UPLOAD_MB
        ):

            await query.edit_message_text(

                "📦 Video is too large for Telegram.\n\n"

                f"Original size: "
                f"{file_size_mb:.2f} MB\n"

                f"Target size: "
                f"{COMPRESSION_TARGET_MB:.0f} MB\n\n"

                "🗜️ Automatically compressing...\n"
                "Please wait."
            )

            print()
            print("=" * 60)
            print("AUTOMATIC COMPRESSION")
            print("=" * 60)

            compressed_path = await asyncio.to_thread(

                compress_video,

                file_path,

                COMPRESSION_TARGET_MB
            )

            if not compressed_path:

                raise RuntimeError(
                    "Compression returned no file."
                )

            if not os.path.exists(
                compressed_path
            ):

                raise FileNotFoundError(
                    "Compressed file was not created."
                )

            compressed_size = os.path.getsize(
                compressed_path
            )

            compressed_mb = (
                compressed_size /
                (1024 * 1024)
            )

            print(
                "Compressed size:",
                f"{compressed_mb:.2f} MB"
            )

            # =================================================
            # SECOND COMPRESSION IF NECESSARY
            # =================================================

            if compressed_mb > MAX_UPLOAD_MB:

                print(
                    "First compression was still too large."
                )

                await query.edit_message_text(

                    "🗜️ First compression wasn't enough.\n\n"

                    f"Current size: "
                    f"{compressed_mb:.2f} MB\n\n"

                    "🔄 Applying stronger compression..."
                )

                second_compressed_path = (
                    await asyncio.to_thread(

                        compress_video,

                        compressed_path,

                        40.0
                    )
                )

                if second_compressed_path:

                    if os.path.exists(
                        compressed_path
                    ):

                        try:

                            os.remove(
                                compressed_path
                            )

                        except Exception:
                            pass

                    compressed_path = (
                        second_compressed_path
                    )

                    compressed_size = os.path.getsize(
                        compressed_path
                    )

                    compressed_mb = (
                        compressed_size /
                        (1024 * 1024)
                    )

                    print(
                        "Second compression size:",
                        f"{compressed_mb:.2f} MB"
                    )

            # =================================================
            # FINAL SIZE CHECK
            # =================================================

            if compressed_mb > MAX_UPLOAD_MB:

                raise RuntimeError(

                    "The video could not be compressed "
                    f"below {MAX_UPLOAD_MB:.0f} MB.\n\n"

                    f"Final size: "
                    f"{compressed_mb:.2f} MB\n\n"

                    "Please select a lower video quality "
                    "and try again."
                )

            # =================================================
            # IMPORTANT:
            # SEND COMPRESSED FILE
            # =================================================

            file_path = compressed_path

            extension = ".mp4"

            print(
                "Using compressed file:",
                file_path
            )

            await query.edit_message_text(

                "✅ Compression complete!\n\n"

                f"📦 Final size: "
                f"{compressed_mb:.2f} MB\n\n"

                "📤 Sending video to Telegram..."
            )

        else:

            # =================================================
            # ORIGINAL FILE IS SMALL ENOUGH
            # =================================================

            await query.edit_message_text(

                "📤 Sending video to Telegram...\n\n"

                f"📦 Size: "
                f"{file_size_mb:.2f} MB"
            )

        # =================================================
        # FINAL SAFETY CHECK
        # =================================================

        final_size = os.path.getsize(
            file_path
        )

        final_size_mb = (
            final_size /
            (1024 * 1024)
        )

        print()
        print("=" * 60)
        print("FINAL UPLOAD CHECK")
        print("=" * 60)

        print(
            "File:",
            file_path
        )

        print(
            "Final size:",
            f"{final_size_mb:.2f} MB"
        )

        if final_size_mb > MAX_UPLOAD_MB:

            raise RuntimeError(

                "Upload cancelled because the final "
                f"file is {final_size_mb:.2f} MB, "
                f"which exceeds the safe "
                f"{MAX_UPLOAD_MB:.0f} MB limit."
            )

        # =================================================
        # VIDEO
        # =================================================

        if extension in VIDEO_EXTENSIONS:

            with open(
                file_path,
                "rb"
            ) as video:

                await query.message.reply_video(

                    video=video,

                    read_timeout=600,

                    write_timeout=600,

                    connect_timeout=60,

                    pool_timeout=60,

                    supports_streaming=True
                )

        # =================================================
        # IMAGE
        # =================================================

        elif extension in {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
            ".gif",
        }:

            with open(
                file_path,
                "rb"
            ) as image:

                await query.message.reply_photo(

                    photo=image,

                    read_timeout=300,

                    write_timeout=300,

                    connect_timeout=60,

                    pool_timeout=60
                )

        # =================================================
        # OTHER FILE
        # =================================================

        else:

            with open(
                file_path,
                "rb"
            ) as document:

                await query.message.reply_document(

                    document=document,

                    read_timeout=600,

                    write_timeout=600,

                    connect_timeout=60,

                    pool_timeout=60
                )

        # =================================================
        # SUCCESS
        # =================================================

        print()
        print("=" * 60)
        print("TELEGRAM UPLOAD SUCCESSFUL")
        print("=" * 60)

        context.user_data.clear()

        await query.message.reply_text(

            "✅ Done!\n\n"
            "Choose another platform:",

            reply_markup=main_menu_keyboard()
        )

    # =====================================================
    # ERROR
    # =====================================================

    except Exception as error:

        print()
        print("=" * 60)
        print("DOWNLOAD/UPLOAD ERROR")
        print("=" * 60)

        print(
            str(error)
        )

        print("=" * 60)

        try:

            await query.message.reply_text(

                "❌ Download/upload failed.\n\n"
                f"{str(error)}",

                reply_markup=main_menu_keyboard()
            )

        except Exception as reply_error:

            print(
                "Could not send error message:",
                reply_error
            )

    # =====================================================
    # CLEANUP
    # =====================================================

    finally:

        files_to_delete = set()

        if file_path:

            files_to_delete.add(
                file_path
            )

        if compressed_path:

            files_to_delete.add(
                compressed_path
            )

        for path in files_to_delete:

            try:

                if os.path.exists(
                    path
                ):

                    os.remove(
                        path
                    )

                    print(
                        "Temporary file deleted:",
                        path
                    )

            except Exception as cleanup_error:

                print(
                    "Cleanup error:",
                    cleanup_error
                )


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print("=" * 70)
    print("STARTING TELEGRAM BOT")
    print("=" * 70)

    print(
        "Python:",
        os.sys.executable
    )

    print(
        "Telegram safe upload size:",
        f"{MAX_UPLOAD_MB:.2f} MB"
    )

    print(
        "Compression target:",
        f"{COMPRESSION_TARGET_MB:.2f} MB"
    )

    print("=" * 70)
    print()

    application = (

        Application.builder()

        .token(
            BOT_TOKEN
        )

        .connect_timeout(
            60
        )

        .read_timeout(
            600
        )

        .write_timeout(
            600
        )

        .pool_timeout(
            60
        )

        .build()
    )

    # =====================================================
    # START
    # =====================================================

    application.add_handler(

        CommandHandler(
            "start",
            start
        )
    )

    # =====================================================
    # BACK
    # =====================================================

    application.add_handler(

        CallbackQueryHandler(
            back_to_menu,
            pattern="^back_to_menu$"
        )
    )

    # =====================================================
    # PLATFORM
    # =====================================================

    application.add_handler(

        CallbackQueryHandler(

            platform_selected,

            pattern=(
                "^(youtube|tiktok|facebook|x|whatsapp)$"
            )
        )
    )

    # =====================================================
    # QUALITY
    # =====================================================

    application.add_handler(

        CallbackQueryHandler(

            quality_selected,

            pattern=(
                r"^quality_"
                r"(144|240|360|480|540|720|1080|1440|2160|best)$"
            )
        )
    )

    # =====================================================
    # URL / TEXT
    # =====================================================

    application.add_handler(

        MessageHandler(

            filters.TEXT
            &
            ~filters.COMMAND,

            handle_url
        )
    )

    # =====================================================
    # RUN
    # =====================================================

    print(
        "Bot is running..."
    )

    print()

    application.run_polling(
        drop_pending_updates=True
    )


# =========================================================
# START PROGRAM
# =========================================================

if __name__ == "__main__":

    main()