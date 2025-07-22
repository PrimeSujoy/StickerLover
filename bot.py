#!/usr/bin/env python3
"""
Telegram Sticker Converter Bot

This bot converts:
- Stickers to Images/Videos
- Images/Videos to Stickers

Features:
- Lightning-fast conversion
- Video duration validation (max 2 seconds for stickers)
- Automatic format detection and conversion
"""

import os
import asyncio
import tempfile
import logging
from pathlib import Path
from typing import Optional

from telegram import Update, File
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from PIL import Image
from moviepy.editor import VideoFileClip
import aiofiles
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token from environment
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

# Temporary directory for file processing
TEMP_DIR = Path("/tmp/bot_files")
TEMP_DIR.mkdir(exist_ok=True)


class StickerConverter:
    """Handles all sticker conversion operations"""
    
    @staticmethod
    async def sticker_to_image(file_path: str, output_path: str) -> bool:
        """Convert sticker (WEBP) to image (PNG)"""
        try:
            with Image.open(file_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img, mask=img.split()[-1])
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                img.save(output_path, 'PNG', optimize=True)
                return True
        except Exception as e:
            logger.error(f"Error converting sticker to image: {e}")
            return False
    
    @staticmethod
    async def image_to_sticker(file_path: str, output_path: str) -> bool:
        """Convert image to sticker (WEBP)"""
        try:
            with Image.open(file_path) as img:
                # Resize to sticker dimensions (max 512x512)
                img.thumbnail((512, 512), Image.Resampling.LANCZOS)
                
                # Convert to RGBA for sticker format
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                img.save(output_path, 'WEBP', optimize=True, quality=95)
                return True
        except Exception as e:
            logger.error(f"Error converting image to sticker: {e}")
            return False
    
    @staticmethod
    async def video_to_sticker(file_path: str, output_path: str) -> tuple[bool, Optional[str]]:
        """Convert video to animated sticker (WEBM)"""
        try:
            with VideoFileClip(file_path) as video:
                # Check duration (max 2 seconds for Telegram stickers)
                if video.duration > 2.0:
                    return False, "❌ Video is too long! Telegram stickers must be 2 seconds or less."
                
                # Resize to sticker dimensions
                video_resized = video.resize(height=512)
                
                # Write as WEBM for animated stickers
                video_resized.write_videofile(
                    output_path,
                    codec='libvpx-vp9',
                    audio=False,
                    verbose=False,
                    logger=None
                )
                
                return True, None
        except Exception as e:
            logger.error(f"Error converting video to sticker: {e}")
            return False, f"❌ Error processing video: {str(e)}"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    welcome_message = """🎉 Welcome to the Sticker Converter Bot!

Just send me a sticker or a photo/video, and I'll magically convert it for you:

📸 Sticker ➡️ Image/Video

🖼️ Image/Video ➡️ Sticker

No commands needed — just drop it in and watch the magic happen! ✨"""
    
    await update.message.reply_text(welcome_message)


async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle sticker messages - convert to image/video"""
    try:
        sticker = update.message.sticker
        
        # Send processing message
        processing_msg = await update.message.reply_text("🔄 Converting sticker...")
        
        # Download sticker
        file: File = await sticker.get_file()
        
        # Create temporary file paths
        input_path = TEMP_DIR / f"sticker_{update.message.message_id}.webp"
        
        # Download file
        await file.download_to_drive(input_path)
        
        if sticker.is_animated:
            # Convert animated sticker to video
            output_path = TEMP_DIR / f"video_{update.message.message_id}.mp4"
            
            # For animated stickers, we'll send the original file as video
            # Since it's already in a video format (WEBM/TGS)
            await update.message.reply_video(
                video=input_path,
                caption="🎬 Here's your sticker as a video!"
            )
        else:
            # Convert static sticker to image
            output_path = TEMP_DIR / f"image_{update.message.message_id}.png"
            
            success = await StickerConverter.sticker_to_image(str(input_path), str(output_path))
            
            if success:
                await update.message.reply_photo(
                    photo=output_path,
                    caption="🖼️ Here's your sticker as an image!"
                )
            else:
                await update.message.reply_text("❌ Failed to convert sticker. Please try again.")
        
        # Delete processing message
        await processing_msg.delete()
        
        # Cleanup temporary files
        input_path.unlink(missing_ok=True)
        if 'output_path' in locals():
            output_path.unlink(missing_ok=True)
            
    except Exception as e:
        logger.error(f"Error handling sticker: {e}")
        await update.message.reply_text("❌ An error occurred while processing your sticker.")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle photo messages - convert to sticker"""
    try:
        photo = update.message.photo[-1]  # Get highest resolution
        
        # Send processing message
        processing_msg = await update.message.reply_text("🔄 Converting image to sticker...")
        
        # Download photo
        file: File = await photo.get_file()
        
        # Create temporary file paths
        input_path = TEMP_DIR / f"photo_{update.message.message_id}.jpg"
        output_path = TEMP_DIR / f"sticker_{update.message.message_id}.webp"
        
        # Download file
        await file.download_to_drive(input_path)
        
        # Convert to sticker
        success = await StickerConverter.image_to_sticker(str(input_path), str(output_path))
        
        if success:
            await update.message.reply_sticker(
                sticker=output_path,
                caption="📸 Here's your image as a sticker!"
            )
        else:
            await update.message.reply_text("❌ Failed to convert image. Please try again.")
        
        # Delete processing message
        await processing_msg.delete()
        
        # Cleanup temporary files
        input_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)
        
    except Exception as e:
        logger.error(f"Error handling photo: {e}")
        await update.message.reply_text("❌ An error occurred while processing your image.")


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle video messages - convert to animated sticker"""
    try:
        video = update.message.video
        
        # Send processing message
        processing_msg = await update.message.reply_text("🔄 Converting video to sticker...")
        
        # Download video
        file: File = await video.get_file()
        
        # Create temporary file paths
        input_path = TEMP_DIR / f"video_{update.message.message_id}.mp4"
        output_path = TEMP_DIR / f"sticker_{update.message.message_id}.webm"
        
        # Download file
        await file.download_to_drive(input_path)
        
        # Convert to animated sticker
        success, error_msg = await StickerConverter.video_to_sticker(str(input_path), str(output_path))
        
        if success:
            await update.message.reply_video(
                video=output_path,
                caption="🎬 Here's your video as an animated sticker!"
            )
        else:
            await update.message.reply_text(error_msg or "❌ Failed to convert video. Please try again.")
        
        # Delete processing message
        await processing_msg.delete()
        
        # Cleanup temporary files
        input_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)
        
    except Exception as e:
        logger.error(f"Error handling video: {e}")
        await update.message.reply_text("❌ An error occurred while processing your video.")


async def handle_video_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle video note messages - convert to animated sticker"""
    try:
        video_note = update.message.video_note
        
        # Send processing message
        processing_msg = await update.message.reply_text("🔄 Converting video note to sticker...")
        
        # Download video note
        file: File = await video_note.get_file()
        
        # Create temporary file paths
        input_path = TEMP_DIR / f"video_note_{update.message.message_id}.mp4"
        output_path = TEMP_DIR / f"sticker_{update.message.message_id}.webm"
        
        # Download file
        await file.download_to_drive(input_path)
        
        # Convert to animated sticker
        success, error_msg = await StickerConverter.video_to_sticker(str(input_path), str(output_path))
        
        if success:
            await update.message.reply_video(
                video=output_path,
                caption="🎬 Here's your video note as an animated sticker!"
            )
        else:
            await update.message.reply_text(error_msg or "❌ Failed to convert video note. Please try again.")
        
        # Delete processing message
        await processing_msg.delete()
        
        # Cleanup temporary files
        input_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)
        
    except Exception as e:
        logger.error(f"Error handling video note: {e}")
        await update.message.reply_text("❌ An error occurred while processing your video note.")


def main() -> None:
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.VIDEO_NOTE, handle_video_note))
    
    # Start the bot
    logger.info("Starting Telegram Sticker Converter Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

