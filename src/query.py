import os
import sys
import argparse
import datetime
from llama_index.core import VectorStoreIndex, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb
from colorama import init, Fore, Style

# Try absolute import first, then relative import as fallback
try:
    from src.html_report import generate_html_header, generate_html_footer, add_file_to_html, generate_html_report
except ImportError:
    try:
        from html_report import generate_html_header, generate_html_footer, add_file_to_html, generate_html_report
    except ImportError:
        from .html_report import generate_html_header, generate_html_footer, add_file_to_html, generate_html_report

init(autoreset=True)


def create_output_directory():
    """
    Create an output directory with a subdirectory named with the current datetime.

    Returns:
        str: Path to the created output directory
    """
    # Create the main output directory if it doesn't exist
    output_dir = os.path.join(os.getcwd(), 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Create a subdirectory with the current datetime
    now = datetime.datetime.now()
    datetime_str = now.strftime('%Y-%m-%d_%H-%M-%S')
    run_dir = os.path.join(output_dir, datetime_str)
    os.makedirs(run_dir)

    return run_dir


def find_files_with_extension(directory, extension):
    """
    Recursively find all files with the given extension in the directory and its subdirectories.

    Args:
        directory (str): The directory to search in
        extension (str): The file extension to look for (e.g., '.py')

    Returns:
        list: A list of file paths
    """
    file_paths = []

    # Ensure extension starts with a dot
    if not extension.startswith('.'):
        extension = '.' + extension

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(extension):
                file_paths.append(os.path.join(root, file))

    return file_paths


def process_file(file_path, index, model_name, ollama_url, output_dir, html_content):
    """
    Process a single file for security analysis.

    Args:
        file_path (str): Path to the file to analyze
        index: The vector index for retrieval
        model_name (str): The name of the Ollama model to use
        ollama_url (str): The URL of the Ollama API
        output_dir (str): Directory to save the output
        html_content (list): List to append HTML content to

    Returns:
        bool: True if processing was successful, False otherwise
    """
    try:
        print(f'{Fore.WHITE}{Style.BRIGHT}File process started: {file_path}')
        with open(file_path, 'r') as f:
            code = f.read()

        query = f"""
You are a software security analyst. Use ALL the indexed knowledge to analyze the following code:

{code}

Your objective is to:
- Identify OWASP vulnerabilities.
- Point out common vulnerabilities.
- Suggest security improvements.

If no vulnerabilities are found, explicitly state: "No vulnerabilities detected."

IMPORTANT: always consider the OWASP Top 10 and web application security best practices.
"""

        retriever = index.as_retriever(similarity_top_k=3)
        nodes = retriever.retrieve(query)
        context = '\n'.join([n.get_content() for n in nodes])

        final_prompt = f"""
        You are a software security analyst. Use ALL the indexed knowledge to analyze the following code:

        {code}

        Here is the extracted technical knowledge to assist you:
        {context}

        Your objective is to:
        - Identify OWASP vulnerabilities.
        - Point out common vulnerabilities.
        - Suggest security improvements.

        If no vulnerabilities are found, explicitly state: "No vulnerabilities detected."

        IMPORTANT: always consider the OWASP Top 10 and web application security best practices.
        """

        response = Settings.llm.complete(final_prompt)

        # Add the file analysis to the HTML content
        file_html = add_file_to_html(file_path, response.text)
        html_content.append(file_html)

        print(f'{Fore.WHITE}{Style.BRIGHT}File process finished: {file_path}')

        return True

    except Exception as e:
        print(f'{Fore.RED}{Style.BRIGHT}Error processing {file_path}: {str(e)}')
        return False


def run_query(path, extension=None, model_name='mistral:7b-instruct', ollama_url='http://localhost:11434'):
    """
    Run security analysis on files.

    Args:
        path (str): Path to a file or directory to analyze
        extension (str, optional): File extension to filter by when path is a directory
        model_name (str): The name of the Ollama model to use
        ollama_url (str): The URL of the Ollama API

    Returns:
        bool: True if processing was successful, False otherwise
    """
    if not os.path.exists(path):
        print(f"{Fore.RED}{Style.BRIGHT}Error: Path '{path}' not found.")
        return False

    try:
        # Create output directory with datetime subdirectory
        output_dir = create_output_directory()

        print(f'{Fore.WHITE}{Style.BRIGHT}Using Ollama model {model_name} at {ollama_url}...')
        Settings.llm = Ollama(model=model_name, base_url=ollama_url, request_timeout=300)
        Settings.embed_model = HuggingFaceEmbedding(model_name='sentence-transformers/all-MiniLM-L6-v2')

        print(f'{Fore.WHITE}{Style.BRIGHT}Initializing ChromaDB...')
        chroma_client = chromadb.PersistentClient(path='./chroma_db')
        collection = chroma_client.get_collection('security_docs')

        print(f'{Fore.WHITE}{Style.BRIGHT}Initializing vector store...')
        vector_store = ChromaVectorStore(chroma_collection=collection)

        index = VectorStoreIndex(
            [],
            vector_store=vector_store,
        )

        # Determine files to process
        files_to_process = []
        if os.path.isfile(path):
            files_to_process = [path]
        elif os.path.isdir(path):
            if extension:
                files_to_process = find_files_with_extension(path, extension)
                if not files_to_process:
                    print(
                        f"{Fore.YELLOW}No files with extension '{extension}' found in '{path}' or its subdirectories."
                    )
                    return False
            else:
                print(
                    f'{Fore.RED}{Style.BRIGHT}Error: When specifying a directory, you must also provide a file extension.'
                )
                return False

        print(f'{Fore.WHITE}{Style.BRIGHT}Found {len(files_to_process)} files to process.')

        # Initialize HTML content
        html_content = []

        # Process each file
        success = True
        for file_path in files_to_process:
            file_success = process_file(file_path, index, model_name, ollama_url, output_dir, html_content)
            success = success and file_success

        # Generate and save the HTML report
        if success and html_content:
            report_title = f'SovereignRag - Security Analysis Report - {os.path.basename(path)}'
            html_report = generate_html_report(report_title, html_content)

            # Save the HTML report
            report_path = os.path.join(output_dir, 'report.html')
            with open(report_path, 'w') as f:
                f.write(html_report)

            print(f'{Fore.GREEN}{Style.BRIGHT}Report saved to: {report_path}')

        return success

    except Exception as e:
        print(f'{Fore.RED}{Style.BRIGHT}Error: {str(e)}')
        return False


def main():
    parser = argparse.ArgumentParser(description='Analyze code for security vulnerabilities')
    parser.add_argument(
        '--path',
        '-p',
        type=str,
        required=True,
        help='Path to the source code file or directory to analyze',
    )
    parser.add_argument(
        '--extension',
        '-e',
        type=str,
        help="File extension to filter by when path is a directory (e.g., 'py', 'java')",
    )
    parser.add_argument(
        '--model',
        '-m',
        type=str,
        default='phi3:m1-latest',
        help='Ollama model to use (default: phi3:m1-latest)',
    )
    parser.add_argument(
        '--ollama-url',
        type=str,
        default='http://localhost:11434',
        help='Ollama API URL',
    )
    args = parser.parse_args()

    # If path is a directory, extension is required
    if os.path.isdir(args.path) and not args.extension:
        parser.error('--extension is required when path is a directory')

    success = run_query(args.path, args.extension, args.model, args.ollama_url)
    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()
