#!/usr/bin/env python3
"""
Manual testing script for ArchiveDrop bot.

This script provides guided manual testing procedures to verify
the bot is working correctly in a real Telegram environment.
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path


def print_header(title):
    """Print a formatted header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_step(step_num, title):
    """Print a formatted step."""
    print(f"\n{step_num}. {title}")
    print("-" * (len(str(step_num)) + len(title) + 2))


def wait_for_input(prompt="Press Enter to continue..."):
    """Wait for user input."""
    input(f"\n{prompt}")


def check_environment():
    """Check that required environment variables are set."""
    required_vars = ['BOT_TOKEN', 'STORAGE_DIR']
    missing = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print("ERROR: Missing required environment variables:")
        for var in missing:
            print(f"  - {var}")
        print("\nPlease set these variables or create a .env file.")
        return False
    
    storage_dir = Path(os.getenv('STORAGE_DIR'))
    if not storage_dir.exists():
        print(f"ERROR: Storage directory does not exist: {storage_dir}")
        print("Please create the directory or update STORAGE_DIR.")
        return False
    
    if not os.access(storage_dir, os.W_OK):
        print(f"ERROR: Storage directory is not writable: {storage_dir}")
        print("Please check permissions.")
        return False
    
    print("✓ Environment configuration looks good")
    return True


def get_bot_info():
    """Get information about the bot setup."""
    bot_token = os.getenv('BOT_TOKEN')
    storage_dir = os.getenv('STORAGE_DIR')
    rate_limit = os.getenv('RATE_LIMIT_PER_MIN', '10')
    max_audio = os.getenv('MAX_AUDIO_BYTES', '52428800')
    allowlist = os.getenv('ALLOWLIST', 'None (all users allowed)')
    
    print(f"Bot Token: {bot_token[:10]}...{bot_token[-10:] if bot_token else 'NOT SET'}")
    print(f"Storage Directory: {storage_dir}")
    print(f"Rate Limit: {rate_limit} messages/minute")
    print(f"Max Audio Size: {int(max_audio) // (1024*1024)}MB")
    print(f"Allowlist: {allowlist}")


def test_text_messages():
    """Guide user through text message testing."""
    print_step(1, "Text Message Testing")
    
    print("This test verifies that text messages are properly stored.")
    print("\nInstructions:")
    print("1. Open Telegram and find your bot")
    print("2. Send the /start command to the bot")
    print("3. Send a test text message like: 'Hello, this is a test message'")
    print("4. Send another message with special characters: 'Test with émojis 🤖 and symbols!'")
    
    wait_for_input("Complete the above steps, then press Enter...")
    
    # Check for recent files
    storage_dir = Path(os.getenv('STORAGE_DIR'))
    now = datetime.now()
    today_dir = storage_dir / f"{now.year:04d}" / f"{now.month:02d}" / f"{now.day:02d}"
    
    if not today_dir.exists():
        print("❌ No files found for today. Check if messages were processed.")
        return False
    
    text_files = list(today_dir.glob("*-text.txt"))
    json_files = list(today_dir.glob("*-text.json"))
    
    print(f"\nFound {len(text_files)} text files and {len(json_files)} metadata files")
    
    if text_files:
        print("✓ Text files created successfully")
        # Show content of most recent file
        latest_file = max(text_files, key=lambda f: f.stat().st_mtime)
        print(f"\nMost recent text file: {latest_file.name}")
        with open(latest_file, 'r', encoding='utf-8') as f:
            content = f.read()[:100] + ('...' if len(f.read()) > 100 else '')
            print(f"Content preview: {content}")
        
        # Show metadata
        meta_file = latest_file.with_suffix('.json')
        if meta_file.exists():
            print(f"\nMetadata file: {meta_file.name}")
            with open(meta_file, 'r') as f:
                metadata = json.load(f)
                print("Metadata keys:", list(metadata.keys()))
                print(f"Size: {metadata.get('size')} bytes")
                print(f"Checksum: {metadata.get('checksum', 'N/A')[:16]}...")
    else:
        print("❌ No text files found. Check bot logs for errors.")
        return False
    
    return True


def test_voice_messages():
    """Guide user through voice message testing."""
    print_step(2, "Voice Message Testing")
    
    print("This test verifies that voice messages are properly stored.")
    print("\nInstructions:")
    print("1. In Telegram, hold the microphone button")
    print("2. Record a short voice message (5-10 seconds)")
    print("3. Send the voice message to your bot")
    print("4. Optionally, send another voice message in a different format if your client supports it")
    
    wait_for_input("Complete the above steps, then press Enter...")
    
    # Check for recent audio files
    storage_dir = Path(os.getenv('STORAGE_DIR'))
    now = datetime.now()
    today_dir = storage_dir / f"{now.year:04d}" / f"{now.month:02d}" / f"{now.day:02d}"
    
    audio_extensions = ['*.ogg', '*.mp3', '*.m4a', '*.wav']
    audio_files = []
    for pattern in audio_extensions:
        audio_files.extend(today_dir.glob(f"*-audio.{pattern[2:]}"))
    
    audio_json_files = list(today_dir.glob("*-audio.json"))
    
    print(f"\nFound {len(audio_files)} audio files and {len(audio_json_files)} metadata files")
    
    if audio_files:
        print("✓ Audio files created successfully")
        # Show info about most recent file
        latest_file = max(audio_files, key=lambda f: f.stat().st_mtime)
        print(f"\nMost recent audio file: {latest_file.name}")
        print(f"File size: {latest_file.stat().st_size} bytes")
        
        # Show metadata
        meta_file = latest_file.with_suffix('.json')
        if meta_file.exists():
            print(f"\nMetadata file: {meta_file.name}")
            with open(meta_file, 'r') as f:
                metadata = json.load(f)
                print("Metadata keys:", list(metadata.keys()))
                print(f"Duration: {metadata.get('duration', 'N/A')} seconds")
                print(f"MIME type: {metadata.get('mime_type', 'N/A')}")
                print(f"Checksum: {metadata.get('checksum', 'N/A')[:16]}...")
    else:
        print("❌ No audio files found. Check bot logs for errors.")
        return False
    
    return True


def test_rate_limiting():
    """Guide user through rate limiting testing."""
    print_step(3, "Rate Limiting Testing")
    
    rate_limit = int(os.getenv('RATE_LIMIT_PER_MIN', '10'))
    print(f"Current rate limit: {rate_limit} messages per minute")
    
    print("\nThis test verifies that rate limiting is working correctly.")
    print("Instructions:")
    print(f"1. Send {rate_limit + 1} text messages quickly to your bot")
    print("2. The last message should be rate limited (bot won't respond)")
    print("3. Wait 1 minute and try sending another message")
    print("4. This message should be processed normally")
    
    wait_for_input("Complete the above steps, then press Enter...")
    
    print("Rate limiting behavior observed?")
    response = input("Did the bot stop responding after the rate limit? (y/n): ")
    
    if response.lower().startswith('y'):
        print("✓ Rate limiting appears to be working")
        return True
    else:
        print("❌ Rate limiting may not be working correctly")
        return False


def test_health_command():
    """Guide user through health command testing."""
    print_step(4, "Health Command Testing")
    
    print("This test verifies the bot's health monitoring features.")
    print("\nInstructions:")
    print("1. Send the /health command to your bot")
    print("2. The bot should respond with detailed health information")
    print("3. Check that the response includes:")
    print("   - Bot uptime")
    print("   - Storage status")
    print("   - Session statistics")
    print("   - Rate limiter status")
    
    wait_for_input("Complete the above steps, then press Enter...")
    
    print("Health command working correctly?")
    response = input("Did the bot provide detailed health information? (y/n): ")
    
    if response.lower().startswith('y'):
        print("✓ Health monitoring is working")
        return True
    else:
        print("❌ Health monitoring may have issues")
        return False


def verify_file_structure():
    """Verify the file structure and organization."""
    print_step(5, "File Structure Verification")
    
    storage_dir = Path(os.getenv('STORAGE_DIR'))
    now = datetime.now()
    
    print("Checking file organization...")
    
    # Check date hierarchy
    year_dirs = list(storage_dir.glob("[0-9][0-9][0-9][0-9]"))
    if year_dirs:
        print(f"✓ Found {len(year_dirs)} year directories")
        
        for year_dir in year_dirs:
            month_dirs = list(year_dir.glob("[0-9][0-9]"))
            print(f"  {year_dir.name}/: {len(month_dirs)} month directories")
            
            for month_dir in month_dirs[:3]:  # Show first 3 months
                day_dirs = list(month_dir.glob("[0-9][0-9]"))
                print(f"    {month_dir.name}/: {len(day_dirs)} day directories")
    else:
        print("❌ No date-based directories found")
        return False
    
    # Check filename patterns
    today_dir = storage_dir / f"{now.year:04d}" / f"{now.month:02d}" / f"{now.day:02d}"
    if today_dir.exists():
        all_files = list(today_dir.glob("*"))
        text_files = [f for f in all_files if f.suffix == '.txt']
        audio_files = [f for f in all_files if f.suffix in ['.ogg', '.mp3', '.m4a', '.wav']]
        json_files = [f for f in all_files if f.suffix == '.json']
        
        print(f"\nToday's files ({today_dir.name}):")
        print(f"  Text files: {len(text_files)}")
        print(f"  Audio files: {len(audio_files)}")
        print(f"  Metadata files: {len(json_files)}")
        
        # Verify filename pattern
        for file in (text_files + audio_files)[:3]:  # Check first 3 files
            parts = file.stem.split('-')
            if len(parts) >= 4:
                timestamp, chat_id, msg_id, msg_type = parts[:4]
                print(f"  ✓ {file.name}: valid pattern")
            else:
                print(f"  ❌ {file.name}: invalid pattern")
        
        # Check metadata consistency
        orphaned_files = []
        for content_file in text_files + audio_files:
            meta_file = content_file.with_suffix('.json')
            if not meta_file.exists():
                orphaned_files.append(content_file)
        
        if orphaned_files:
            print(f"❌ Found {len(orphaned_files)} files without metadata")
        else:
            print("✓ All content files have corresponding metadata")
    
    return True


def check_constitutional_compliance():
    """Verify constitutional compliance in stored data."""
    print_step(6, "Constitutional Compliance Check")
    
    print("Checking privacy and security compliance...")
    
    storage_dir = Path(os.getenv('STORAGE_DIR'))
    
    # Check that no personal information is in filenames
    personal_indicators = ['username', 'name', 'user', 'first', 'last', '@']
    problematic_files = []
    
    for file_path in storage_dir.rglob("*"):
        if file_path.is_file():
            filename = file_path.name.lower()
            for indicator in personal_indicators:
                if indicator in filename:
                    problematic_files.append((file_path, indicator))
    
    if problematic_files:
        print(f"❌ Found {len(problematic_files)} files with potential PII in filenames:")
        for file_path, indicator in problematic_files[:5]:  # Show first 5
            print(f"  {file_path.name} (contains: {indicator})")
    else:
        print("✓ No personal information detected in filenames")
    
    # Check metadata files for PII
    json_files = list(storage_dir.rglob("*.json"))
    pii_fields = ['username', 'first_name', 'last_name', 'phone_number', 'email']
    
    pii_violations = []
    for json_file in json_files[:10]:  # Check first 10 metadata files
        try:
            with open(json_file, 'r') as f:
                metadata = json.load(f)
                for field in pii_fields:
                    if field in metadata:
                        pii_violations.append((json_file, field))
        except (json.JSONDecodeError, OSError):
            continue
    
    if pii_violations:
        print(f"❌ Found PII in {len(pii_violations)} metadata files")
    else:
        print("✓ No PII detected in metadata files")
    
    # Check for required metadata fields
    required_fields = ['timestamp', 'message_id', 'chat_id', 'size', 'checksum']
    
    if json_files:
        sample_file = json_files[0]
        try:
            with open(sample_file, 'r') as f:
                metadata = json.load(f)
                missing_fields = [field for field in required_fields if field not in metadata]
                if missing_fields:
                    print(f"❌ Missing required metadata fields: {missing_fields}")
                else:
                    print("✓ All required metadata fields present")
        except (json.JSONDecodeError, OSError):
            print("❌ Could not read sample metadata file")
    
    return len(problematic_files) == 0 and len(pii_violations) == 0


def generate_test_report():
    """Generate a summary test report."""
    print_header("TEST REPORT SUMMARY")
    
    storage_dir = Path(os.getenv('STORAGE_DIR'))
    
    # Count files
    text_files = list(storage_dir.rglob("*-text.txt"))
    audio_files = []
    for ext in ['ogg', 'mp3', 'm4a', 'wav']:
        audio_files.extend(storage_dir.rglob(f"*-audio.{ext}"))
    json_files = list(storage_dir.rglob("*.json"))
    
    total_size = sum(f.stat().st_size for f in text_files + audio_files + json_files)
    
    print(f"Files processed during testing:")
    print(f"  Text messages: {len(text_files)}")
    print(f"  Audio messages: {len(audio_files)}")
    print(f"  Metadata files: {len(json_files)}")
    print(f"  Total storage used: {total_size / (1024*1024):.2f} MB")
    
    # Show recent activity
    if text_files or audio_files:
        all_content_files = text_files + audio_files
        latest_file = max(all_content_files, key=lambda f: f.stat().st_mtime)
        oldest_file = min(all_content_files, key=lambda f: f.stat().st_mtime)
        
        print(f"\nActivity range:")
        print(f"  Oldest file: {datetime.fromtimestamp(oldest_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Latest file: {datetime.fromtimestamp(latest_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\nTesting completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    """Main testing workflow."""
    print_header("ArchiveDrop Manual Testing Script")
    
    print("This script will guide you through manual testing of your ArchiveDrop bot.")
    print("Make sure your bot is running before starting these tests.")
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    print("\nBot Configuration:")
    get_bot_info()
    
    wait_for_input("\nReady to start testing? Press Enter to continue...")
    
    # Run tests
    tests = [
        ("Text Messages", test_text_messages),
        ("Voice Messages", test_voice_messages),
        ("Rate Limiting", test_rate_limiting),
        ("Health Command", test_health_command),
        ("File Structure", verify_file_structure),
        ("Constitutional Compliance", check_constitutional_compliance),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except KeyboardInterrupt:
            print("\n\nTesting interrupted by user.")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with error: {e}")
            results[test_name] = False
    
    # Summary
    print_header("TESTING RESULTS")
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your ArchiveDrop bot is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review the output above and check your bot configuration.")
    
    generate_test_report()


if __name__ == "__main__":
    main()