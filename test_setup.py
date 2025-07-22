#!/usr/bin/env python3
"""
Test script to verify bot setup and dependencies
"""

import sys
import os
from pathlib import Path

def test_dependencies():
    """Test if all required dependencies are installed"""
    print("🔍 Testing dependencies...")
    
    try:
        import telegram
        print("✅ python-telegram-bot installed")
    except ImportError:
        print("❌ python-telegram-bot not found")
        return False
    
    try:
        import PIL
        print("✅ Pillow installed")
    except ImportError:
        print("❌ Pillow not found")
        return False
    
    try:
        import moviepy
        print("✅ MoviePy installed")
    except ImportError:
        print("❌ MoviePy not found")
        return False
    
    try:
        import aiofiles
        print("✅ aiofiles installed")
    except ImportError:
        print("❌ aiofiles not found")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv installed")
    except ImportError:
        print("❌ python-dotenv not found")
        return False
    
    return True

def test_environment():
    """Test environment setup"""
    print("\n🔍 Testing environment...")
    
    # Check if .env file exists
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file found")
        
        # Load and check BOT_TOKEN
        from dotenv import load_dotenv
        load_dotenv()
        
        bot_token = os.getenv('BOT_TOKEN')
        if bot_token and bot_token != 'your_bot_token_here':
            print("✅ BOT_TOKEN configured")
            return True
        else:
            print("❌ BOT_TOKEN not configured properly")
            print("   Please set your bot token in .env file")
            return False
    else:
        print("❌ .env file not found")
        print("   Please copy .env.example to .env and configure BOT_TOKEN")
        return False

def test_file_structure():
    """Test if all required files exist"""
    print("\n🔍 Testing file structure...")
    
    required_files = [
        "bot.py",
        "requirements.txt",
        "Dockerfile",
        ".env.example",
        "README.md"
    ]
    
    all_exist = True
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} missing")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests"""
    print("🚀 Telegram Sticker Bot Setup Test\n")
    
    tests = [
        ("File Structure", test_file_structure),
        ("Dependencies", test_dependencies),
        ("Environment", test_environment)
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        try:
            if not test_func():
                all_passed = False
        except Exception as e:
            print(f"❌ {test_name} test failed: {e}")
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 All tests passed! Your bot is ready to run.")
        print("\nTo start the bot:")
        print("  python bot.py")
        print("\nOr with Docker:")
        print("  docker build -t telegram-sticker-bot .")
        print("  docker run -d --name sticker-bot -e BOT_TOKEN=your_token telegram-sticker-bot")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

