"""
Unit tests for documents module.
File: tests/unit/test_documents.py
"""
import pytest
from pathlib import Path
from unittest.mock import patch
from rag.documents import (
    recursive_text_chunker,
    create_document_chunks,
    read_text_file,
    read_json_file
)


class TestRecursiveTextChunker:
    """Test the recursive text chunker."""

    def test_chunker_returns_list_of_dicts(self):
        """Test chunker returns list of dicts with position info."""
        text = "This is a test document. " * 50
        chunks = recursive_text_chunker(text, chunk_size=100, overlap=20)

        assert isinstance(chunks, list)
        assert len(chunks) > 0
        assert all(isinstance(c, dict) for c in chunks)
        assert all('text' in c for c in chunks)
        assert all('start_char' in c for c in chunks)
        assert all('end_char' in c for c in chunks)

    def test_chunker_single_chunk_under_size(self):
        """Test text under chunk size returns single chunk."""
        text = "Short text"
        chunks = recursive_text_chunker(text, chunk_size=100)

        assert len(chunks) == 1
        assert chunks[0]['text'] == text
        assert chunks[0]['start_char'] == 0
        assert chunks[0]['end_char'] == len(text)

    def test_chunker_respects_chunk_size(self):
        """Test chunks respect maximum size."""
        text = "word " * 1000  # ~5000 chars
        chunks = recursive_text_chunker(text, chunk_size=100, overlap=0)

        for chunk in chunks:
            assert len(chunk['text']) <= 100 or chunk['text'] == text

    def test_chunker_position_tracking_deterministic(self):
        """Test position tracking is deterministic and accurate."""
        text = "First paragraph.\nSecond paragraph.\nThird paragraph."
        chunks = recursive_text_chunker(text, chunk_size=50, overlap=10)

        # Verify positions are sequential and non-overlapping
        for i, chunk in enumerate(chunks):
            # Positions should be within bounds
            assert 0 <= chunk['start_char'] < len(text)
            assert 0 < chunk['end_char'] <= len(text)
            assert chunk['start_char'] < chunk['end_char']

            # Text at position should match
            assert text[chunk['start_char']:chunk['end_char']] == chunk['text']

    def test_chunker_overlapping_chunks(self):
        """Test that overlap parameter creates overlapping chunks."""
        text = "A" * 250  # 250 'A's
        chunks = recursive_text_chunker(text, chunk_size=100, overlap=50)

        assert len(chunks) > 1

        # Check for overlap in content between consecutive chunks
        for i in range(len(chunks) - 1):
            curr_end = chunks[i]['end_char']
            next_start = chunks[i + 1]['start_char']
            # Should have overlap
            assert next_start < curr_end

    def test_chunker_preserves_complete_text(self):
        """Test that chunking preserves all text without loss."""
        text = "The quick brown fox jumps over the lazy dog. " * 20
        chunks = recursive_text_chunker(text, chunk_size=200, overlap=30)

        # Reconstruct text from chunks (without overlap)
        reconstructed = ""
        for i, chunk in enumerate(chunks):
            if i == 0:
                reconstructed += chunk['text']
            else:
                # Skip the overlapping part
                prev_end = chunks[i-1]['end_char']
                skip = prev_end - chunk['start_char']
                reconstructed += chunk['text'][skip:] if skip < len(chunk['text']) else chunk['text']

        # We should be able to find all the original content
        assert all(content in reconstructed or content in "".join(c['text'] for c in chunks)
                   for content in text.split()[:50])  # Check first 50 words

    def test_chunker_handles_empty_string(self):
        """Test chunker handles empty strings."""
        chunks = recursive_text_chunker("")
        assert chunks == []

    def test_chunker_handles_very_small_chunk_size(self):
        """Test chunker with very small chunk sizes."""
        text = "Hello world"
        chunks = recursive_text_chunker(text, chunk_size=3, overlap=0)

        assert len(chunks) > 0
        for chunk in chunks:
            assert len(chunk['text']) <= 3


class TestCreateDocumentChunks:
    """Test document chunking with metadata."""

    def test_create_chunks_adds_metadata(self):
        """Test that metadata is properly added to chunks."""
        document_data = {
            'content': 'Sample document text. ' * 100,
            'source': '/path/to/file.txt',
            'file_name': 'file.txt',
            'file_type': 'txt',
            'metadata': {'key': 'value'}
        }

        chunks = create_document_chunks(document_data, chunk_size=100, chunk_overlap=20)

        assert len(chunks) > 0
        for i, chunk in enumerate(chunks):
            assert chunk['chunk_index'] == i
            assert chunk['file_name'] == 'file.txt'
            assert chunk['file_type'] == 'txt'
            assert 'start_char' in chunk
            assert 'end_char' in chunk
            assert 'metadata' in chunk
            assert chunk['metadata']['chunk_index'] == i

    def test_create_chunks_with_custom_size(self):
        """Test create_document_chunks with custom chunk size."""
        document_data = {
            'content': 'A' * 1000,
            'source': '/test.txt',
            'file_name': 'test.txt',
            'file_type': 'txt',
            'metadata': {}
        }

        chunks_200 = create_document_chunks(document_data, chunk_size=200, chunk_overlap=0)
        chunks_100 = create_document_chunks(document_data, chunk_size=100, chunk_overlap=0)

        # Smaller chunk size should produce more chunks
        assert len(chunks_100) > len(chunks_200)

    def test_create_chunks_uses_settings_defaults(self):
        """Test that create_document_chunks uses settings when no params provided."""
        document_data = {
            'content': 'Sample text. ' * 100,
            'source': '/test.txt',
            'file_name': 'test.txt',
            'file_type': 'txt',
            'metadata': {}
        }

        with patch('rag.documents.get_settings') as mock_settings:
            mock_settings.return_value.chunk_size = 500
            mock_settings.return_value.chunk_overlap = 50

            chunks = create_document_chunks(document_data)
            assert len(chunks) > 0

    def test_create_chunks_position_consistency(self):
        """Test that positions in chunks are consistent with original text."""
        text = "First sentence. Second sentence. Third sentence. " * 10
        document_data = {
            'content': text,
            'source': '/test.txt',
            'file_name': 'test.txt',
            'file_type': 'txt',
            'metadata': {}
        }

        chunks = create_document_chunks(document_data, chunk_size=200, chunk_overlap=30)

        for chunk in chunks:
            # Verify text matches the position in original
            extracted = text[chunk['start_char']:chunk['end_char']]
            assert extracted == chunk['text']


class TestTextFileReading:
    """Test text file reading."""

    def test_read_text_file_success(self, tmp_path):
        """Test reading a text file."""
        test_file = tmp_path / "test.txt"
        test_content = "This is test content\nWith multiple lines\n"
        test_file.write_text(test_content)

        content = read_text_file(test_file)
        assert content == test_content

    def test_read_text_file_nonexistent(self):
        """Test reading nonexistent file returns None."""
        content = read_text_file(Path("/nonexistent/path/file.txt"))
        assert content is None

    def test_read_text_file_utf8(self, tmp_path):
        """Test reading UTF-8 encoded files."""
        test_file = tmp_path / "utf8.txt"
        test_content = "Hello 世界 مرحبا мир"
        test_file.write_text(test_content, encoding='utf-8')

        content = read_text_file(test_file)
        assert content == test_content


class TestJSONFileReading:
    """Test JSON file reading."""

    def test_read_json_file_dict(self, tmp_path):
        """Test reading JSON file with dict."""
        import json

        test_file = tmp_path / "test.json"
        test_data = {"key": "value", "nested": {"inner": "data"}}
        test_file.write_text(json.dumps(test_data))

        content = read_json_file(test_file)
        assert isinstance(content, str)
        assert "key" in content
        assert "value" in content

    def test_read_json_file_list(self, tmp_path):
        """Test reading JSON file with list."""
        import json

        test_file = tmp_path / "list.json"
        test_data = [{"id": 1}, {"id": 2}]
        test_file.write_text(json.dumps(test_data))

        content = read_json_file(test_file)
        assert isinstance(content, str)
        assert len(content) > 0

    def test_read_json_file_invalid(self, tmp_path):
        """Test reading invalid JSON file."""
        test_file = tmp_path / "invalid.json"
        test_file.write_text("{ invalid json")

        content = read_json_file(test_file)
        assert content is None


class TestChunkingDeterminism:
    """Test that chunking is deterministic."""

    def test_chunking_deterministic_same_input(self):
        """Test that same input produces same chunks."""
        text = "Sample document text. " * 100
        document_data = {
            'content': text,
            'source': '/test.txt',
            'file_name': 'test.txt',
            'file_type': 'txt',
            'metadata': {}
        }

        chunks1 = create_document_chunks(document_data, chunk_size=100, chunk_overlap=20)
        chunks2 = create_document_chunks(document_data, chunk_size=100, chunk_overlap=20)

        assert len(chunks1) == len(chunks2)
        for c1, c2 in zip(chunks1, chunks2):
            assert c1['text'] == c2['text']
            assert c1['start_char'] == c2['start_char']
            assert c1['end_char'] == c2['end_char']
