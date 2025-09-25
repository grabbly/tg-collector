"""
Integration tests for bot functionality.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram import Bot
from aiogram.types import Message, User, Chat, Update
from src.cli.bot import dp, init_bot, init_rate_limiter


@pytest.fixture
def mock_bot():
    """Create a mock bot for testing."""
    bot = MagicMock(spec=Bot)
    bot.session = MagicMock()
    bot.session.close = AsyncMock()
    return bot


@pytest.fixture
def mock_update_start():
    """Create a mock update with /start command."""
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.from_user = MagicMock(spec=User)
    update.message.from_user.id = 123456789
    update.message.chat = MagicMock(spec=Chat)
    update.message.chat.id = 123456789
    update.message.message_id = 1
    update.message.text = "/start"
    update.message.answer = AsyncMock()
    return update


class TestBotIntegration:
    """Integration tests for bot functionality."""
    
    @pytest.mark.asyncio
    async def test_bot_initialization(self):
        """Test that bot can be initialized with config."""
        with patch('src.cli.bot.get_config') as mock_config:
            mock_config.return_value.bot_token = "test_token"
            
            bot = init_bot()
            assert bot is not None
    
    @pytest.mark.asyncio
    async def test_rate_limiter_initialization(self):
        """Test that rate limiter can be initialized."""
        with patch('src.cli.bot.get_config') as mock_config:
            mock_config.return_value.rate_limit_per_min = 10
            
            rate_limiter = init_rate_limiter()
            assert rate_limiter is not None
    
    @pytest.mark.asyncio
    async def test_dispatcher_handles_start_command(self, mock_update_start):
        """Test that dispatcher correctly routes /start command."""
        with patch('src.cli.bot.log_event'), \
             patch('src.cli.bot.safe_answer') as mock_safe_answer:
            
            # Process the update through dispatcher
            await dp.feed_update(mock_bot(), mock_update_start)
            
            # Verify safe_answer was called (meaning handle_start was executed)
            mock_safe_answer.assert_called_once()
            
            # Verify the message contains Ukrainian welcome
            call_args = mock_safe_answer.call_args[0]
            welcome_text = call_args[1]
            assert "Вітаю!" in welcome_text
    
    @pytest.mark.asyncio
    async def test_bot_handles_text_message(self):
        """Test that bot can handle regular text messages."""
        # Create mock update with text message
        update = MagicMock(spec=Update)
        update.message = MagicMock(spec=Message)
        update.message.from_user = MagicMock(spec=User)
        update.message.from_user.id = 123456789
        update.message.chat = MagicMock(spec=Chat)
        update.message.chat.id = 123456789
        update.message.message_id = 2
        update.message.text = "Hello bot!"
        update.message.voice = None
        update.message.answer = AsyncMock()
        
        with patch('src.cli.bot.log_event'), \
             patch('src.cli.bot.save_text') as mock_save_text, \
             patch('src.cli.bot.safe_answer') as mock_safe_answer, \
             patch('src.cli.bot.rate_limiter') as mock_rate_limiter:
            
            # Mock rate limiter to allow request
            mock_rate_limiter.is_allowed.return_value.allowed = True
            
            # Mock successful save
            mock_save_text.return_value = ("text.txt", "metadata.json")
            
            # Process the update
            await dp.feed_update(mock_bot(), update)
            
            # Verify text was saved
            mock_save_text.assert_called_once()
            
            # Verify confirmation message was sent
            mock_safe_answer.assert_called_once()
            confirmation_text = mock_safe_answer.call_args[0][1]
            assert "Text saved" in confirmation_text


class TestBotErrorHandling:
    """Test bot error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_bot_handles_api_error_gracefully(self, mock_update_start):
        """Test that bot handles Telegram API errors gracefully."""
        with patch('src.cli.bot.log_event') as mock_log, \
             patch('src.cli.bot.safe_answer') as mock_safe_answer:
            
            # Simulate API error in safe_answer
            mock_safe_answer.side_effect = Exception("API Error")
            
            # This should not raise an exception
            try:
                await dp.feed_update(mock_bot(), mock_update_start)
            except Exception:
                pytest.fail("Bot should handle API errors gracefully")
    
    @pytest.mark.asyncio
    async def test_bot_handles_unicode_message(self):
        """Test that bot can handle Unicode messages without errors."""
        # Create update with Unicode text
        update = MagicMock(spec=Update)
        update.message = MagicMock(spec=Message)
        update.message.from_user = MagicMock(spec=User)
        update.message.from_user.id = 123456789
        update.message.chat = MagicMock(spec=Chat)
        update.message.chat.id = 123456789
        update.message.message_id = 3
        update.message.text = "Привіт! 👋 Це повідомлення українською з емодзі 🤖"
        update.message.voice = None
        update.message.answer = AsyncMock()
        
        with patch('src.cli.bot.log_event'), \
             patch('src.cli.bot.save_text') as mock_save_text, \
             patch('src.cli.bot.safe_answer'), \
             patch('src.cli.bot.rate_limiter') as mock_rate_limiter:
            
            mock_rate_limiter.is_allowed.return_value.allowed = True
            mock_save_text.return_value = ("text.txt", "metadata.json")
            
            # This should not raise encoding errors
            try:
                await dp.feed_update(mock_bot(), update)
            except (UnicodeEncodeError, UnicodeDecodeError):
                pytest.fail("Bot should handle Unicode messages without encoding errors")