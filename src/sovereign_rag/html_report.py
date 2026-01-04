import datetime


def generate_html_header(title):
    """
    Generate the HTML header with CSS styles for the report.

    Args:
        title (str): The title of the HTML page

    Returns:
        str: HTML header content
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SovereignRag{title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }}
        .file-item {{
            margin-bottom: 15px;
            border: 1px solid #ddd;
            border-radius: 4px;
            overflow: hidden;
        }}
        .file-header {{
            background-color: #f1f1f1;
            padding: 10px 15px;
            cursor: pointer;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .file-header:hover {{
            background-color: #e9e9e9;
        }}
        .file-content {{
            padding: 15px;
            display: none;
            border-top: 1px solid #ddd;
            white-space: pre-wrap;
        }}
        .file-content.active {{
            display: block;
        }}
        .toggle-icon {{
            font-size: 18px;
        }}
        .timestamp {{
            color: #666;
            font-size: 14px;
            margin-top: 5px;
        }}
        pre {{
            background-color: #f8f8f8;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <p class="timestamp">Generated on: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
"""


def generate_html_footer():
    """
    Generate the HTML footer with JavaScript for the collapsible sections.

    Returns:
        str: HTML footer content
    """
    return """
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const fileHeaders = document.querySelectorAll('.file-header');

                fileHeaders.forEach(header => {
                    header.addEventListener('click', function() {
                        const content = this.nextElementSibling;
                        const icon = this.querySelector('.toggle-icon');

                        if (content.style.display === 'block') {
                            content.style.display = 'none';
                            icon.textContent = '+';
                        } else {
                            content.style.display = 'block';
                            icon.textContent = '-';
                        }
                    });
                });
            });
        </script>
    </div>
</body>
</html>
"""


def add_file_to_html(file_path, analysis_result):
    """
    Generate HTML for a file analysis result with a collapsible section.

    Args:
        file_path (str): Path to the analyzed file
        analysis_result (str): The analysis result text

    Returns:
        str: HTML content for the file analysis
    """
    return f"""
        <div class="file-item">
            <div class="file-header">
                <span>{file_path}</span>
                <span class="toggle-icon">+</span>
            </div>
            <div class="file-content">
                <pre>{analysis_result}</pre>
            </div>
        </div>
"""


def generate_html_report(title, html_content):
    """
    Generate a complete HTML report.

    Args:
        title (str): The title of the HTML report
        html_content (list): List of HTML content sections to include in the report

    Returns:
        str: Complete HTML report
    """
    html_report = generate_html_header(title)
    html_report += "".join(html_content)
    html_report += generate_html_footer()
    return html_report
