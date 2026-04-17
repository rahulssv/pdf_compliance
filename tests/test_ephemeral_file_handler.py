"""Unit tests for in-memory file handler."""

from urllib.parse import quote

import pytest

from src.services.ephemeral_file_handler import EphemeralFileHandler, MemoryAwareFileHandler


def test_load_from_absolute_path(temp_pdf_file):
    handler = EphemeralFileHandler(max_memory_mb=10)
    buffer, filename = handler._load_to_memory(str(temp_pdf_file))

    assert filename == temp_pdf_file.name
    assert buffer.getvalue().startswith(b"%PDF")
    handler.cleanup_all()


def test_load_from_file_url(temp_pdf_file):
    handler = EphemeralFileHandler(max_memory_mb=10)
    file_url = f"file://{quote(str(temp_pdf_file))}"
    buffer, filename = handler._load_to_memory(file_url)

    assert filename == temp_pdf_file.name
    assert len(buffer.getvalue()) > 0
    handler.cleanup_all()


def test_rejects_missing_file():
    handler = EphemeralFileHandler(max_memory_mb=10)
    with pytest.raises(FileNotFoundError):
        handler._load_to_memory("/tmp/not-a-real-file.pdf")


def test_enforces_memory_limit(temp_pdf_file):
    handler = EphemeralFileHandler(max_memory_mb=0)
    with pytest.raises(ValueError, match="File too large"):
        handler._load_to_memory(str(temp_pdf_file))


def test_context_manager_auto_cleans_buffers(temp_pdf_file):
    handler = EphemeralFileHandler(max_memory_mb=10)
    with handler.ephemeral_file_context(str(temp_pdf_file)) as (buffer, filename):
        assert filename == temp_pdf_file.name
        assert not buffer.closed
        usage = handler.get_memory_usage()
        assert usage["active_buffers"] == 1

    usage = handler.get_memory_usage()
    assert usage["active_buffers"] == 0


def test_cleanup_all_closes_open_buffers(temp_pdf_file):
    handler = EphemeralFileHandler(max_memory_mb=10)
    b1, _ = handler._load_to_memory(str(temp_pdf_file))
    b2, _ = handler._load_to_memory(str(temp_pdf_file))
    handler._active_buffers.extend([b1, b2])

    handler.cleanup_all()

    assert b1.closed
    assert b2.closed
    assert handler.get_memory_usage()["active_buffers"] == 0


def test_memory_aware_handler_tracks_processed_files(temp_pdf_file):
    handler = MemoryAwareFileHandler(max_memory_mb=10, enable_monitoring=True)
    with handler.ephemeral_file_context(str(temp_pdf_file)):
        pass
    with handler.ephemeral_file_context(str(temp_pdf_file)):
        pass

    stats = handler.get_statistics()
    assert stats["files_processed"] == 2
    assert stats["total_bytes_processed"] > 0
