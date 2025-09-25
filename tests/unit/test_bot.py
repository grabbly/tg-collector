"""
Unit tests for the Telegram bot functionality.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.types import Message, User, Chat
from src.cli.bot import handle_start, safe_answer


@pytest.fixture
def mock_message():
    """Create a mock message for testing."""
    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 123456789
    message.chat = MagicMock(spec=Chat)
    message.chat.id = 123456789
    message.message_id = 1
    message.answer = AsyncMock()
    return message


@pytest.fixture
def mock_message_sync():
    """Create a mock message with sync answer for testing."""
    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 123456789
    message.chat = MagicMock(spec=Chat)
    message.chat.id = 123456789
    message.message_id = 1
    message.answer = MagicMock()  # Non-async mock for testing fallback
    return message


class TestSafeAnswer:
    """Test the safe_answer function."""
    
    @pytest.mark.asyncio
    async def test_safe_answer_async_success(self, mock_message):
        """Test safe_answer with async message.answer."""
        await safe_answer(mock_message, "Test message")
        mock_message.answer.assert_called_once_with("Test message")
    
    @pytest.mark.asyncio
    async def test_safe_answer_sync_fallback(self, mock_message_sync):
        """Test safe_answer with sync message.answer fallback."""
        await safe_answer(mock_message_sync, "Test message")
        mock_message_sync.answer.assert_called_once_with("Test message")
    
    @pytest.mark.asyncio
    async def test_safe_answer_with_api_error(self, mock_message):
        """Test safe_answer when Telegram API returns an error."""
        # Simulate API error
        mock_message.answer.side_effect = Exception("API Error: Forbidden")
        
        with patch('src.cli.bot.log_event') as mock_log:
            await safe_answer(mock_message, "Test message")
            
            # Check that error was logged
            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            assert kwargs['event'] == 'message_send_error'
            assert 'API Error: Forbidden' in kwargs['message']
    
    @pytest.mark.asyncio
    async def test_safe_answer_with_unicode(self, mock_message):
        """Test safe_answer with Unicode characters."""
        unicode_text = "Вітаю! 👋 Це тестове повідомлення з емодзі."
        await safe_answer(mock_message, unicode_text)
        mock_message.answer.assert_called_once_with(unicode_text)


class TestHandleStart:
    """Test the handle_start function."""
    
    @pytest.mark.asyncio
    async def test_handle_start_success(self, mock_message):
        """Test successful handling of /start command."""
        with patch('src.cli.bot.log_event') as mock_log, \
             patch('src.cli.bot.safe_answer') as mock_safe_answer:
            
            await handle_start(mock_message)
            
            # Check that events were logged
            log_calls = [call[1] for call in mock_log.call_args_list]
            events = [call['event'] for call in log_calls]
            
            assert 'command_start' in events
            assert 'sending_welcome_message' in events
            assert 'welcome_message_sent' in events
            
            # Check that safe_answer was called with Ukrainian message
            mock_safe_answer.assert_called_once()
            call_args = mock_safe_answer.call_args[0]
            assert call_args[0] == mock_message
            welcome_text = call_args[1]
            assert "Вітаю!" in welcome_text
            assert "Андрій Сазонов" in welcome_text
            assert "InnSaga Business Club" in welcome_text
    
    @pytest.mark.asyncio
    async def test_handle_start_with_safe_answer_error(self, mock_message):
        """Test handle_start when safe_answer fails."""
        with patch('src.cli.bot.log_event') as mock_log, \
             patch('src.cli.bot.safe_answer') as mock_safe_answer:
            
            # Simulate safe_answer error
            mock_safe_answer.side_effect = Exception("Send failed")
            
            await handle_start(mock_message)
            
            # Check that error was logged
            log_calls = [call[1] for call in mock_log.call_args_list]
            events = [call['event'] for call in log_calls]
            
            assert 'command_start' in events
            assert 'sending_welcome_message' in events
            assert 'start_response_error' in events
    
    @pytest.mark.asyncio 
    async def test_handle_start_message_content(self, mock_message):
        """Test that the welcome message contains all required content."""
        with patch('src.cli.bot.log_event'), \
             patch('src.cli.bot.safe_answer') as mock_safe_answer:
            
            await handle_start(mock_message)
            
            # Get the welcome message text
            welcome_text = mock_safe_answer.call_args[0][1]
            
            # Check required content
            assert "Вітаю!" in welcome_text
            assert "👋" in welcome_text
            assert "Андрій Сазонов" in welcome_text
            assert "InnSaga Business Club" in welcome_text
            assert "штучного інтелекту" in welcome_text
            assert "голосове" in welcome_text
            assert "Дякую!" in welcome_text
            
            # Check HTML formatting is present
            assert "<b>InnSaga Business Club</b>" in welcome_text


class TestWelcomeMessageEncoding:
    """Test Unicode and encoding issues in welcome message."""
    
    def test_welcome_message_unicode_integrity(self):
        """Test that welcome message doesn't contain corrupted Unicode."""
        # Import the actual welcome text from the module
        from src.cli.bot import handle_start
        import inspect
        
        # Get source code and check for corrupted characters
        source = inspect.getsource(handle_start)
        
        # Check that there are no Unicode replacement characters
        assert "�" not in source, "Found corrupted Unicode character in source"
        
        # Check that emoji is properly encoded
        assert "👋" in source or "\\U0001f44b" in source, "Missing wave emoji"
    
    @pytest.mark.asyncio
    async def test_welcome_message_encoding(self, mock_message):
        """Test that welcome message can be properly encoded/decoded."""
        with patch('src.cli.bot.log_event'), \
             patch('src.cli.bot.safe_answer') as mock_safe_answer:
            
            await handle_start(mock_message)
            welcome_text = mock_safe_answer.call_args[0][1]
            
            # Test that text can be encoded/decoded without errors
            try:
                encoded = welcome_text.encode('utf-8')
                decoded = encoded.decode('utf-8')
                assert decoded == welcome_text
            except UnicodeEncodeError:
                pytest.fail("Welcome message contains characters that cannot be UTF-8 encoded")
            except UnicodeDecodeError:
                pytest.fail("Welcome message cannot be UTF-8 decoded")