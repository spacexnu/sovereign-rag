import unittest
from unittest.mock import MagicMock, mock_open, patch

from sovereign_rag.query import (
    _run_git,
    add_file_to_html,
    create_output_directory,
    filter_to_changed_files,
    find_files_with_extension,
    generate_html_footer,
    generate_html_header,
    process_file,
    run_query,
)


class TestCreateOutputDirectory(unittest.TestCase):
    """Test the create_output_directory function."""

    @patch("sovereign_rag.query.os.path.exists")
    @patch("sovereign_rag.query.os.makedirs")
    @patch("sovereign_rag.query.os.getcwd")
    @patch("sovereign_rag.query.datetime")
    def test_create_output_directory(self, mock_datetime, mock_getcwd, mock_makedirs, mock_exists):
        """Test creating an output directory."""
        # Set up mocks
        mock_exists.return_value = False
        mock_getcwd.return_value = "/test/path"
        mock_datetime.datetime.now.return_value.strftime.return_value = "2023-01-01_12-00-00"

        # Call the function
        result = create_output_directory()

        # Verify the result
        expected_output_dir = "/test/path/output"
        expected_run_dir = "/test/path/output/2023-01-01_12-00-00"

        mock_exists.assert_called_once_with(expected_output_dir)
        mock_makedirs.assert_any_call(expected_output_dir)
        mock_makedirs.assert_any_call(expected_run_dir, exist_ok=True)
        self.assertEqual(result, expected_run_dir)


class TestGenerateHtmlHeader(unittest.TestCase):
    """Test the generate_html_header function."""

    @patch("sovereign_rag.html_report.datetime")
    def test_generate_html_header(self, mock_datetime):
        """Test generating an HTML header."""
        # Set up mocks
        mock_datetime.datetime.now.return_value.strftime.return_value = "2023-01-01 12:00:00"

        # Call the function
        result = generate_html_header("Test Title")

        # Verify the result
        self.assertIn("<title>SovereignRagTest Title</title>", result)
        self.assertIn("<h1>Test Title</h1>", result)
        self.assertIn("Generated on: 2023-01-01 12:00:00", result)


class TestGenerateHtmlFooter(unittest.TestCase):
    """Test the generate_html_footer function."""

    def test_generate_html_footer(self):
        """Test generating an HTML footer."""
        # Call the function
        result = generate_html_footer()

        # Verify the result
        self.assertIn("<script>", result)
        self.assertIn("</html>", result)


class TestAddFileToHtml(unittest.TestCase):
    """Test the add_file_to_html function."""

    def test_add_file_to_html(self):
        """Test adding a file to HTML."""
        # Call the function
        result = add_file_to_html("test_file.py", "Test analysis result")

        # Verify the result
        self.assertIn("test_file.py", result)
        self.assertIn("Test analysis result", result)
        self.assertIn('<div class="file-item">', result)


class TestFindFilesWithExtension(unittest.TestCase):
    """Test the find_files_with_extension function."""

    @patch("sovereign_rag.query.os.walk")
    def test_find_files_with_extension(self, mock_walk):
        """Test finding files with a specific extension."""
        # Set up mocks
        mock_walk.return_value = [
            ("/test/dir", ["subdir"], ["file1.py", "file2.txt", "file3.py"]),
            ("/test/dir/subdir", [], ["file4.py", "file5.txt"]),
        ]

        # Call the function
        result = find_files_with_extension("/test/dir", "py")

        # Verify the result
        expected = ["/test/dir/file1.py", "/test/dir/file3.py", "/test/dir/subdir/file4.py"]
        self.assertEqual(result, expected)


class TestRunGit(unittest.TestCase):
    """Test the Git subprocess wrapper."""

    @patch("sovereign_rag.query.subprocess.run")
    def test_run_git_trusts_target_repo_per_invocation(self, mock_run):
        """Every Git call must pass `-c safe.directory=*` so bind-mounted repos with
        a different owner are not rejected as dubious ownership."""
        mock_run.return_value = MagicMock(stdout="/repo\n")

        result = _run_git(["rev-parse", "--show-toplevel"], "/repo")

        self.assertEqual(result, ["/repo"])
        args, kwargs = mock_run.call_args
        self.assertEqual(
            args[0],
            ["git", "-c", "safe.directory=*", "rev-parse", "--show-toplevel"],
        )
        self.assertEqual(kwargs["cwd"], "/repo")


class TestChangedFileFiltering(unittest.TestCase):
    """Test filtering analysis targets to Git-changed files."""

    @patch("sovereign_rag.query.find_changed_files")
    def test_filter_to_changed_files_keeps_only_changed_candidates(self, mock_find_changed_files):
        """Only files already selected by path/extension should be kept."""
        candidates = [
            "/repo/src/file1.py",
            "/repo/src/file2.py",
            "/repo/src/file3.py",
        ]
        mock_find_changed_files.return_value = [
            "/repo/src/file2.py",
            "/repo/docs/notes.md",
        ]

        result = filter_to_changed_files(candidates, "/repo/src", changed_base="origin/main")

        self.assertEqual(result, ["/repo/src/file2.py"])
        mock_find_changed_files.assert_called_once_with("/repo/src", changed_base="origin/main", staged=False)

    @patch("sovereign_rag.query.find_changed_files")
    def test_filter_to_changed_files_supports_staged_mode(self, mock_find_changed_files):
        """Staged mode is passed through for pre-commit usage."""
        candidates = ["/repo/src/file1.py"]
        mock_find_changed_files.return_value = ["/repo/src/file1.py"]

        result = filter_to_changed_files(candidates, "/repo/src", staged=True)

        self.assertEqual(result, ["/repo/src/file1.py"])
        mock_find_changed_files.assert_called_once_with("/repo/src", changed_base="HEAD", staged=True)

    @patch("sovereign_rag.query.os.walk")
    def test_find_files_with_extension_with_dot(self, mock_walk):
        """Test finding files with a specific extension that includes a dot."""
        # Set up mocks
        mock_walk.return_value = [
            ("/test/dir", ["subdir"], ["file1.py", "file2.txt", "file3.py"]),
            ("/test/dir/subdir", [], ["file4.py", "file5.txt"]),
        ]

        # Call the function
        result = find_files_with_extension("/test/dir", ".py")

        # Verify the result
        expected = ["/test/dir/file1.py", "/test/dir/file3.py", "/test/dir/subdir/file4.py"]
        self.assertEqual(result, expected)


class TestProcessFile(unittest.TestCase):
    """Test the process_file function."""

    @patch("sovereign_rag.query.open", new_callable=mock_open, read_data="Test code")
    @patch("sovereign_rag.query.Settings")
    def test_process_file_success(self, mock_settings, mock_file_open):
        """Test successful processing of a file."""
        # Set up mocks
        mock_index = MagicMock()
        mock_retriever = MagicMock()
        mock_node = MagicMock()
        mock_node.get_content.return_value = "Test context"
        mock_node.metadata = {"source": "owasp_top_10.md"}
        mock_retriever.retrieve.return_value = [mock_node]
        mock_index.as_retriever.return_value = mock_retriever

        mock_response = MagicMock()
        mock_response.text = "Test analysis result"
        mock_settings.llm.complete.return_value = mock_response

        html_content = []

        # Call the function
        result = process_file(
            "test_file.py", mock_index, "test_model", "http://localhost:11434", "/test/output", html_content
        )

        # Verify the result
        self.assertTrue(result)
        mock_file_open.assert_called_once_with("test_file.py", encoding="utf-8", errors="replace")
        mock_index.as_retriever.assert_called_once_with(similarity_top_k=3)
        mock_retriever.retrieve.assert_called_once()
        mock_settings.llm.complete.assert_called_once()
        self.assertEqual(len(html_content), 1)
        self.assertIn("test_file.py", html_content[0])
        self.assertIn("Test analysis result", html_content[0])
        # The retrieved source document should be cited in the report.
        self.assertIn("owasp_top_10.md", html_content[0])

    @patch("sovereign_rag.query.open", new_callable=mock_open)
    def test_process_file_error(self, mock_file_open):
        """Test error handling in process_file."""
        # Set up mock to raise an exception
        mock_file_open.side_effect = Exception("Test error")

        html_content = []

        # Call the function
        result = process_file(
            "test_file.py", MagicMock(), "test_model", "http://localhost:11434", "/test/output", html_content
        )

        # Verify the result
        self.assertFalse(result)
        mock_file_open.assert_called_once_with("test_file.py", encoding="utf-8", errors="replace")
        self.assertEqual(len(html_content), 0)


class TestRunQuery(unittest.TestCase):
    """Test the run_query function."""

    @patch("sovereign_rag.query.os.path.exists")
    @patch("sovereign_rag.query.os.path.isfile")
    @patch("sovereign_rag.query.os.path.isdir")
    @patch("sovereign_rag.query.find_files_with_extension")
    @patch("sovereign_rag.query.create_output_directory")
    @patch("sovereign_rag.query.Settings")
    @patch("sovereign_rag.query.Ollama")
    @patch("sovereign_rag.query.HuggingFaceEmbedding")
    @patch("sovereign_rag.query.chromadb.PersistentClient")
    @patch("sovereign_rag.query.ChromaVectorStore")
    @patch("sovereign_rag.query.VectorStoreIndex")
    @patch("sovereign_rag.query.process_file")
    @patch("sovereign_rag.query.open", new_callable=mock_open)
    def test_run_query_directory(
        self,
        mock_file_open,
        mock_process_file,
        mock_vector_store_index,
        mock_chroma_vector_store,
        mock_chroma_client,
        mock_huggingface,
        mock_ollama,
        mock_settings,
        mock_create_output_directory,
        mock_find_files,
        mock_isdir,
        mock_isfile,
        mock_exists,
    ):
        """Test run_query with a directory path."""
        # Set up mocks
        mock_exists.return_value = True
        mock_isfile.return_value = False
        mock_isdir.return_value = True
        mock_find_files.return_value = ["test_dir/file1.py", "test_dir/file2.py"]
        mock_create_output_directory.return_value = "/test/output/2023-01-01_12-00-00"

        mock_collection = MagicMock()
        mock_client = MagicMock()
        mock_client.get_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client

        mock_vector_store = MagicMock()
        mock_chroma_vector_store.return_value = mock_vector_store

        mock_index = MagicMock()
        mock_vector_store_index.return_value = mock_index

        mock_process_file.return_value = True

        # Call the function
        result = run_query("test_dir", "py", "test_model", "http://localhost:11434")

        # Verify the result
        self.assertTrue(result)
        mock_exists.assert_called_once_with("test_dir")
        mock_isfile.assert_called_once_with("test_dir")
        mock_isdir.assert_called_once_with("test_dir")
        mock_find_files.assert_called_once_with("test_dir", "py")
        mock_create_output_directory.assert_called_once()
        mock_ollama.assert_called_once_with(model="test_model", base_url="http://localhost:11434", request_timeout=300)
        mock_huggingface.assert_called_once_with(model_name="sentence-transformers/all-MiniLM-L6-v2")
        mock_chroma_client.assert_called_once_with(path="./chroma_db")
        mock_client.get_collection.assert_called_once_with("security_docs")
        mock_chroma_vector_store.assert_called_once_with(chroma_collection=mock_collection)
        mock_vector_store_index.assert_called_once_with([], vector_store=mock_vector_store)
        self.assertEqual(mock_process_file.call_count, 2)

    @patch("sovereign_rag.query.os.path.exists")
    @patch("sovereign_rag.query.os.path.isfile")
    @patch("sovereign_rag.query.os.path.isdir")
    @patch("sovereign_rag.query.find_files_with_extension")
    @patch("sovereign_rag.query.filter_to_changed_files")
    @patch("sovereign_rag.query.create_output_directory")
    @patch("sovereign_rag.query.Ollama")
    def test_run_query_changed_only_no_matches_skips_model_initialization(
        self,
        mock_ollama,
        mock_create_output_directory,
        mock_filter_to_changed_files,
        mock_find_files,
        mock_isdir,
        mock_isfile,
        mock_exists,
    ):
        """No matching changed files should be a successful no-op."""
        mock_exists.return_value = True
        mock_isfile.return_value = False
        mock_isdir.return_value = True
        mock_find_files.return_value = ["test_dir/file1.py"]
        mock_filter_to_changed_files.return_value = []

        result = run_query("test_dir", "py", "test_model", "http://localhost:11434", changed_only=True)

        self.assertTrue(result)
        mock_filter_to_changed_files.assert_called_once_with(
            ["test_dir/file1.py"],
            "test_dir",
            changed_base="HEAD",
            staged=False,
        )
        mock_create_output_directory.assert_not_called()
        mock_ollama.assert_not_called()

    @patch("sovereign_rag.query.os.path.exists")
    def test_run_query_path_not_found(self, mock_exists):
        """Test run_query when the path doesn't exist."""
        # Set up mocks
        mock_exists.return_value = False

        # Call the function
        result = run_query("nonexistent_path")

        # Verify the result
        self.assertFalse(result)
        mock_exists.assert_called_once_with("nonexistent_path")


if __name__ == "__main__":
    unittest.main()
