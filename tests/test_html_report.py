import unittest
from unittest.mock import patch, mock_open
import os
import sys
import datetime

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.html_report import (
    generate_html_header,
    generate_html_footer,
    add_file_to_html,
    generate_html_report,
)


class TestGenerateHtmlHeader(unittest.TestCase):
    """Test the generate_html_header function."""

    @patch('src.html_report.datetime')
    def test_generate_html_header(self, mock_datetime):
        """Test generating an HTML header."""
        # Set up mocks
        mock_datetime.datetime.now.return_value.strftime.return_value = '2023-01-01 12:00:00'

        # Call the function
        result = generate_html_header('Test Title')

        # Verify the result
        self.assertIn('<title>SovereignRagTest Title</title>', result)
        self.assertIn('<h1>Test Title</h1>', result)
        self.assertIn('Generated on: 2023-01-01 12:00:00', result)


class TestGenerateHtmlFooter(unittest.TestCase):
    """Test the generate_html_footer function."""

    def test_generate_html_footer(self):
        """Test generating an HTML footer."""
        # Call the function
        result = generate_html_footer()

        # Verify the result
        self.assertIn('<script>', result)
        self.assertIn('</html>', result)


class TestAddFileToHtml(unittest.TestCase):
    """Test the add_file_to_html function."""

    def test_add_file_to_html(self):
        """Test adding a file to HTML."""
        # Call the function
        result = add_file_to_html('test_file.py', 'Test analysis result')

        # Verify the result
        self.assertIn('test_file.py', result)
        self.assertIn('Test analysis result', result)
        self.assertIn('<div class="file-item">', result)


class TestGenerateHtmlReport(unittest.TestCase):
    """Test the generate_html_report function."""

    @patch('src.html_report.generate_html_header')
    @patch('src.html_report.generate_html_footer')
    def test_generate_html_report(self, mock_footer, mock_header):
        """Test generating a complete HTML report."""
        # Set up mocks
        mock_header.return_value = '<header>Test Header</header>'
        mock_footer.return_value = '<footer>Test Footer</footer>'

        # Create test content
        html_content = ['<content>Test Content 1</content>', '<content>Test Content 2</content>']

        # Call the function
        result = generate_html_report('Test Report', html_content)

        # Verify the result
        mock_header.assert_called_once_with('Test Report')
        mock_footer.assert_called_once()
        self.assertEqual(
            result,
            '<header>Test Header</header><content>Test Content 1</content><content>Test Content 2</content><footer>Test Footer</footer>',
        )


if __name__ == '__main__':
    unittest.main()
