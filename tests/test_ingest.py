import unittest
from unittest.mock import MagicMock, patch

from sovereign_rag.ingest import (
    clean_text,
    find_source_files,
    index_documents,
    is_relevant_sentence,
    preprocess_markdown,
    preprocess_pdf,
    run_ingest,
    strip_markdown,
)


class TestCleanText(unittest.TestCase):
    """Test the clean_text function."""

    def test_clean_text_removes_extra_newlines(self):
        """Test that clean_text removes extra newlines."""
        text = "Hello\n\nWorld"
        expected = "Hello\nWorld"
        self.assertEqual(clean_text(text), expected)

    def test_clean_text_removes_extra_spaces(self):
        """Test that clean_text removes extra spaces."""
        text = "Hello    World"
        expected = "Hello World"
        self.assertEqual(clean_text(text), expected)

    def test_clean_text_removes_page_numbers(self):
        """Test that clean_text removes page numbers."""
        text = "Hello World\nPage 1 of 10"
        expected = "Hello World"
        self.assertEqual(clean_text(text), expected)

    def test_clean_text_strips_whitespace(self):
        """Test that clean_text strips whitespace."""
        text = "  Hello World  "
        expected = "Hello World"
        self.assertEqual(clean_text(text), expected)


class TestIsRelevantSentence(unittest.TestCase):
    """Test the is_relevant_sentence function."""

    @patch("sovereign_rag.ingest.spacy")
    def test_short_sentence_is_not_relevant(self, mock_spacy):
        """Test that a short sentence is not considered relevant."""
        # Create a mock sentence
        mock_sent = MagicMock()
        mock_sent.text = "Short"

        # The function checks if the length is < 20
        self.assertFalse(is_relevant_sentence(mock_sent))

    @patch("sovereign_rag.ingest.spacy")
    def test_sentence_without_verb_is_not_relevant(self, mock_spacy):
        """Test that a sentence without a verb is not considered relevant."""
        # Create a mock sentence with tokens that don't have VERB pos
        mock_sent = MagicMock()
        mock_sent.text = "This is a sentence that is long enough to be relevant."

        # Create mock tokens without VERB pos
        mock_token1 = MagicMock()
        mock_token1.pos_ = "NOUN"
        mock_token2 = MagicMock()
        mock_token2.pos_ = "DET"

        # Set up the mock sentence to return the mock tokens
        mock_sent.__iter__.return_value = [mock_token1, mock_token2]

        self.assertFalse(is_relevant_sentence(mock_sent))

    @patch("sovereign_rag.ingest.spacy")
    def test_relevant_sentence(self, mock_spacy):
        """Test that a relevant sentence is identified correctly."""
        # Create a mock sentence
        mock_sent = MagicMock()
        mock_sent.text = "This is a sentence that is long enough to be relevant."

        # Create mock tokens with one VERB pos
        mock_token1 = MagicMock()
        mock_token1.pos_ = "NOUN"
        mock_token2 = MagicMock()
        mock_token2.pos_ = "VERB"

        # Set up the mock sentence to return the mock tokens
        mock_sent.__iter__.return_value = [mock_token1, mock_token2]

        self.assertTrue(is_relevant_sentence(mock_sent))

    @patch("sovereign_rag.ingest.spacy")
    def test_verbless_technical_phrase_is_relevant(self, mock_spacy):
        """Verb-less OWASP-style phrases (e.g. vuln names) are kept when noun-rich."""
        # "Broken Access Control" has no verb but is a meaningful control title.
        mock_sent = MagicMock()
        mock_sent.text = "Broken Access Control"

        # Two proper nouns, no verb.
        mock_token1 = MagicMock(pos_="PROPN", is_alpha=True)
        mock_token2 = MagicMock(pos_="ADJ", is_alpha=True)
        mock_token3 = MagicMock(pos_="PROPN", is_alpha=True)
        mock_sent.__iter__.return_value = [mock_token1, mock_token2, mock_token3]

        self.assertTrue(is_relevant_sentence(mock_sent))


class TestPreprocessPDF(unittest.TestCase):
    """Test the preprocess_pdf function."""

    @patch("sovereign_rag.ingest.fitz.open")
    @patch("sovereign_rag.ingest.tqdm")
    @patch("sovereign_rag.ingest.spacy")
    def test_preprocess_pdf_success(self, mock_spacy, mock_tqdm, mock_fitz_open):
        """Test successful preprocessing of a PDF."""
        # Set up mock document
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "This is a test page."
        mock_doc.__iter__.return_value = [mock_page]
        mock_fitz_open.return_value = mock_doc

        # Set up mock NLP processing
        mock_nlp = MagicMock()
        mock_spacy_doc = MagicMock()
        mock_sent = MagicMock()
        mock_sent.text = "This is a test page."

        # Create mock tokens with one VERB pos
        mock_token1 = MagicMock()
        mock_token1.pos_ = "NOUN"
        mock_token2 = MagicMock()
        mock_token2.pos_ = "VERB"

        # Set up the mock sentence to return the mock tokens
        mock_sent.__iter__.return_value = [mock_token1, mock_token2]

        mock_spacy_doc.sents = [mock_sent]
        mock_nlp.return_value = mock_spacy_doc

        # Set up mock spacy
        mock_spacy.load.return_value = mock_nlp

        # Set up mock tqdm
        mock_tqdm.return_value = [mock_page]

        # Call the function with a monkeypatch for the global nlp variable
        with patch.dict("sovereign_rag.ingest.__dict__", {"nlp": mock_nlp}):
            # Call the function
            result = preprocess_pdf("test.pdf")

            # Verify the result
            self.assertEqual(result, ["This is a test page."])
            mock_fitz_open.assert_called_once_with("test.pdf")
            mock_page.get_text.assert_called_once()

    @patch("sovereign_rag.ingest.fitz.open")
    def test_preprocess_pdf_error(self, mock_fitz_open):
        """Test error handling in preprocess_pdf."""
        # Set up mock to raise an exception
        mock_fitz_open.side_effect = Exception("Test error")

        # Call the function
        result = preprocess_pdf("test.pdf")

        # Verify the result
        self.assertEqual(result, [])
        mock_fitz_open.assert_called_once_with("test.pdf")


class TestStripMarkdown(unittest.TestCase):
    """Test the strip_markdown function."""

    def test_removes_heading_markers(self):
        self.assertEqual(strip_markdown("# Broken Access Control").strip(), "Broken Access Control")

    def test_keeps_link_text_drops_target(self):
        self.assertEqual(strip_markdown("See [the cheat sheet](https://owasp.org).").strip(), "See the cheat sheet.")

    def test_removes_fenced_code_blocks(self):
        text = "Intro\n```python\nprint('x')\n```\nOutro"
        result = strip_markdown(text)
        self.assertNotIn("print", result)
        self.assertIn("Intro", result)
        self.assertIn("Outro", result)

    def test_removes_emphasis_markers(self):
        self.assertEqual(strip_markdown("**bold** and _italic_"), "bold and italic")


class TestPreprocessMarkdown(unittest.TestCase):
    """Test the preprocess_markdown function."""

    @patch("sovereign_rag.ingest.spacy")
    def test_preprocess_markdown_success(self, mock_spacy):
        """Test successful preprocessing of a Markdown file."""
        mock_nlp = MagicMock()
        mock_spacy_doc = MagicMock()
        mock_sent = MagicMock()
        mock_sent.text = "This is a relevant sentence."

        mock_token1 = MagicMock()
        mock_token1.pos_ = "NOUN"
        mock_token2 = MagicMock()
        mock_token2.pos_ = "VERB"
        mock_sent.__iter__.return_value = [mock_token1, mock_token2]

        mock_spacy_doc.sents = [mock_sent]
        mock_nlp.return_value = mock_spacy_doc

        with patch("builtins.open", unittest.mock.mock_open(read_data="# Title\nThis is a relevant sentence.")):
            with patch.dict("sovereign_rag.ingest.__dict__", {"nlp": mock_nlp}):
                result = preprocess_markdown("test.md")

        self.assertEqual(result, ["This is a relevant sentence."])

    def test_preprocess_markdown_error(self):
        """Test error handling in preprocess_markdown."""
        with patch("builtins.open", side_effect=Exception("Test error")):
            result = preprocess_markdown("test.md")
        self.assertEqual(result, [])


class TestIndexDocuments(unittest.TestCase):
    """Test the index_documents function."""

    @patch("sovereign_rag.ingest.os.path.exists")
    @patch("sovereign_rag.ingest.os.makedirs")
    def test_index_documents_directory_not_exists(self, mock_makedirs, mock_exists):
        """Test index_documents when the directory doesn't exist."""
        # Set up mocks
        mock_exists.return_value = False

        # Call the function
        index_documents("test_dir")

        # Verify the result
        mock_exists.assert_called_once_with("test_dir")
        mock_makedirs.assert_called_once_with("test_dir")

    @patch("sovereign_rag.ingest.os.path.exists")
    @patch("sovereign_rag.ingest.find_source_files")
    def test_index_documents_no_pdf_files(self, mock_find_source_files, mock_exists):
        """Test index_documents when there are no PDF files."""
        # Set up mocks
        mock_exists.return_value = True
        mock_find_source_files.return_value = []

        # Call the function
        index_documents("test_dir")

        # Verify the result
        mock_exists.assert_called_once_with("test_dir")
        mock_find_source_files.assert_called_once_with("test_dir")

    @patch("sovereign_rag.ingest.os.path.exists")
    @patch("sovereign_rag.ingest.find_source_files")
    @patch("sovereign_rag.ingest.os.path.relpath")
    @patch("sovereign_rag.ingest.preprocess_pdf")
    def test_index_documents_with_pdf_files(self, mock_preprocess, mock_relpath, mock_find_source_files, mock_exists):
        """Test index_documents with PDF files."""
        # Set up mocks
        mock_exists.return_value = True
        mock_find_source_files.return_value = ["test_dir/file1.pdf", "test_dir/subdir/file2.pdf"]
        mock_relpath.side_effect = ["file1.pdf", "subdir/file2.pdf"]
        mock_preprocess.return_value = ["Chunk 1", "Chunk 2"]

        # Mock model and collection
        mock_model = MagicMock()
        mock_model.encode.return_value = [0.1, 0.2, 0.3]

        mock_collection = MagicMock()

        # Patch the global variables
        with patch.dict("sovereign_rag.ingest.__dict__", {"model": mock_model, "collection": mock_collection}):
            # Call the function
            index_documents("test_dir")

            # Verify the result
            mock_exists.assert_called_once_with("test_dir")
            mock_find_source_files.assert_called_once_with("test_dir")
            self.assertEqual(mock_relpath.call_count, 2)
            self.assertEqual(mock_preprocess.call_count, 2)
            self.assertEqual(mock_model.encode.call_count, 4)  # 2 files * 2 chunks
            self.assertEqual(mock_collection.add.call_count, 4)  # 2 files * 2 chunks


class TestFindSourceFiles(unittest.TestCase):
    """Test recursive source discovery."""

    @patch("sovereign_rag.ingest.os.walk")
    def test_find_source_files_recurses_and_skips_hidden_dirs(self, mock_walk):
        mock_walk.return_value = [
            ("docs", [".git", "nested"], ["root.md", "notes.txt"]),
            ("docs/nested", [], ["guide.pdf", "extra.MD"]),
        ]

        result = find_source_files("docs")

        self.assertEqual(result, ["docs/root.md", "docs/nested/extra.MD", "docs/nested/guide.pdf"])
        self.assertEqual(mock_walk.return_value[0][1], ["nested"])


class TestRunIngest(unittest.TestCase):
    """Test the run_ingest function."""

    @patch("sovereign_rag.ingest.spacy.load")
    @patch("sovereign_rag.ingest.SentenceTransformer")
    @patch("sovereign_rag.ingest.chromadb.PersistentClient")
    @patch("sovereign_rag.ingest.index_documents")
    def test_run_ingest_success(
        self, mock_index_documents, mock_chroma_client, mock_sentence_transformer, mock_spacy_load
    ):
        """Test successful run_ingest."""
        # Set up mocks
        mock_collection = MagicMock()
        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client

        # Call the function
        result = run_ingest("test_dir", "test_model")

        # Verify the result
        self.assertTrue(result)
        mock_spacy_load.assert_called_once_with("en_core_web_sm")
        mock_sentence_transformer.assert_called_once_with("test_model")
        mock_chroma_client.assert_called_once_with(path="./chroma_db")
        mock_client.get_or_create_collection.assert_called_once_with("security_docs")
        mock_index_documents.assert_called_once_with("test_dir")

    @patch("sovereign_rag.ingest.spacy.load")
    def test_run_ingest_error(self, mock_spacy_load):
        """Test error handling in run_ingest."""
        # Set up mock to raise an exception
        mock_spacy_load.side_effect = Exception("Test error")

        # Call the function
        result = run_ingest("test_dir", "test_model")

        # Verify the result
        self.assertFalse(result)
        mock_spacy_load.assert_called_once_with("en_core_web_sm")


if __name__ == "__main__":
    unittest.main()
