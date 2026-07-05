import argparse
import datetime
import os
import subprocess
import sys

import chromadb
from colorama import Fore, Style, init
from llama_index.core import Settings, VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.chroma import ChromaVectorStore

# Try absolute import first, then relative import as fallback
try:
    from src.html_report import add_file_to_html, generate_html_footer, generate_html_header, generate_html_report
except ImportError:
    try:
        from .html_report import (
            add_file_to_html,
            generate_html_footer,  # noqa: F401 - re-exported for compatibility with existing imports/tests.
            generate_html_header,  # noqa: F401 - re-exported for compatibility with existing imports/tests.
            generate_html_report,
        )
    except ImportError:
        from .html_report import add_file_to_html, generate_html_report

init(autoreset=True)


def create_output_directory():
    """
    Create an output directory with a subdirectory named with the current datetime.

    Returns:
        str: Path to the created output directory
    """
    # Create the main output directory if it doesn't exist
    output_dir = os.path.join(os.getcwd(), "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Create a subdirectory with the current datetime
    now = datetime.datetime.now()
    datetime_str = now.strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = os.path.join(output_dir, datetime_str)
    os.makedirs(run_dir, exist_ok=True)

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
    if not extension.startswith("."):
        extension = "." + extension

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(extension):
                file_paths.append(os.path.join(root, file))

    return file_paths


def _run_git(args, cwd):
    """Run a Git command and return stdout lines.

    SovereignRAG is meant to be pointed at arbitrary project directories, which are
    often bind-mounted with a different owner than the process (e.g. host uid vs.
    root in Docker). Git would reject those as "dubious ownership", so every command
    trusts its target via a per-invocation `-c safe.directory=*`. This is scoped to
    the git processes spawned here — it sets no global/system config.
    """
    result = subprocess.run(
        ["git", "-c", "safe.directory=*", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def find_git_root(path):
    """Return the Git root for path, or None when path is outside a repository."""
    cwd = path if os.path.isdir(path) else os.path.dirname(path) or "."
    try:
        roots = _run_git(["rev-parse", "--show-toplevel"], cwd)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return roots[0] if roots else None


def find_changed_files(path, changed_base="HEAD", staged=False):
    """Return changed files under path as absolute paths.

    The default mode compares the working tree against changed_base and includes
    untracked files. staged=True is intended for pre-commit hooks and only
    considers files in the index.
    """
    git_root = find_git_root(path)
    if not git_root:
        raise RuntimeError(f"Path '{path}' is not inside a Git repository, or Git is not available.")

    path_abs = os.path.abspath(path)
    pathspec = os.path.relpath(path_abs, git_root)
    if pathspec == ".":
        pathspec = "."

    if staged:
        changed = _run_git(["diff", "--cached", "--name-only", "--diff-filter=ACMR", "--", pathspec], git_root)
    else:
        changed = _run_git(["diff", "--name-only", "--diff-filter=ACMR", changed_base, "--", pathspec], git_root)
        changed.extend(_run_git(["ls-files", "--others", "--exclude-standard", "--", pathspec], git_root))

    changed_abs = []
    seen = set()
    for file_path in changed:
        absolute_path = os.path.abspath(os.path.join(git_root, file_path))
        if absolute_path in seen or not os.path.isfile(absolute_path):
            continue
        seen.add(absolute_path)
        changed_abs.append(absolute_path)

    return changed_abs


def filter_to_changed_files(files_to_process, path, changed_base="HEAD", staged=False):
    """Keep only files that Git reports as changed."""
    changed_files = set(find_changed_files(path, changed_base=changed_base, staged=staged))
    return [file_path for file_path in files_to_process if os.path.abspath(file_path) in changed_files]


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
        print(f"{Fore.WHITE}{Style.BRIGHT}File process started: {file_path}")
        with open(file_path, encoding="utf-8", errors="replace") as f:
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

        # Build the context with an explicit source label per chunk so the model
        # can cite where each piece of knowledge came from. The source filename is
        # stored as chunk metadata at ingest time; fall back to "unknown source".
        context_blocks = []
        sources = []
        for n in nodes:
            source = n.metadata.get("source", "unknown source") if n.metadata else "unknown source"
            if source not in sources:
                sources.append(source)
            context_blocks.append(f"[Source: {source}]\n{n.get_content()}")
        context = "\n\n".join(context_blocks)

        final_prompt = f"""
        You are a software security analyst. Use ALL the indexed knowledge to analyze the following code:

        {code}

        Here is the extracted technical knowledge to assist you. Each block is prefixed
        with its source document in the form [Source: <document>]:
        {context}

        Your objective is to:
        - Identify OWASP vulnerabilities.
        - Point out common vulnerabilities.
        - Suggest security improvements.

        For EVERY vulnerability you report, you MUST include:
        - A description of the problem.
        - A suggested fix.
        - The source: cite the exact source document name (from the [Source: ...] labels
          above) that the information was drawn from. If no provided source supports the
          finding, write "Source: general security knowledge".

        If no vulnerabilities are found, explicitly state: "No vulnerabilities detected."

        IMPORTANT: always consider the OWASP Top 10 and web application security best practices.
        """

        response = Settings.llm.complete(final_prompt)

        # Add the file analysis to the HTML content, including the retrieved sources
        file_html = add_file_to_html(file_path, response.text, sources)
        html_content.append(file_html)

        print(f"{Fore.WHITE}{Style.BRIGHT}File process finished: {file_path}")

        return True

    except Exception as e:
        print(f"{Fore.RED}{Style.BRIGHT}Error processing {file_path}: {str(e)}")
        return False


def run_query(
    path,
    extension=None,
    model_name="mistral:7b-instruct",
    ollama_url="http://localhost:11434",
    num_ctx=None,
    changed_only=False,
    changed_base="HEAD",
    staged=False,
):
    """
    Run security analysis on files.

    Args:
        path (str): Path to a file or directory to analyze
        extension (str, optional): File extension to filter by when path is a directory
        model_name (str): The name of the Ollama model to use
        ollama_url (str): The URL of the Ollama API
        num_ctx (int, optional): Ollama context window size. Smaller values reduce KV-cache
            VRAM usage so the model fits on the GPU; None uses the model's default.
        changed_only (bool): Only analyze files changed in Git.
        changed_base (str): Git ref used as the base for changed_only when staged=False.
        staged (bool): Only analyze staged files; useful for pre-commit hooks.

    Returns:
        bool: True if processing was successful, False otherwise
    """
    if not os.path.exists(path):
        print(f"{Fore.RED}{Style.BRIGHT}Error: Path '{path}' not found.")
        return False

    try:
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
                    f"{Fore.RED}{Style.BRIGHT}Error: When specifying a directory, you must also provide a "
                    "file extension."
                )
                return False

        if changed_only or staged:
            files_to_process = filter_to_changed_files(
                files_to_process,
                path,
                changed_base=changed_base,
                staged=staged,
            )
            changed_label = "staged" if staged else f"changed against {changed_base}"
            if not files_to_process:
                print(f"{Fore.YELLOW}No {changed_label} files matched the requested path/extension.")
                return True

        print(f"{Fore.WHITE}{Style.BRIGHT}Found {len(files_to_process)} files to process.")

        # Create output directory with datetime subdirectory
        output_dir = create_output_directory()

        print(f"{Fore.WHITE}{Style.BRIGHT}Using Ollama model {model_name} at {ollama_url}...")
        llm_kwargs = {"additional_kwargs": {"num_ctx": num_ctx}} if num_ctx else {}
        Settings.llm = Ollama(model=model_name, base_url=ollama_url, request_timeout=300, **llm_kwargs)
        Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

        print(f"{Fore.WHITE}{Style.BRIGHT}Initializing ChromaDB...")
        chroma_client = chromadb.PersistentClient(path="./chroma_db")
        collection = chroma_client.get_collection("security_docs")

        print(f"{Fore.WHITE}{Style.BRIGHT}Initializing vector store...")
        vector_store = ChromaVectorStore(chroma_collection=collection)

        index = VectorStoreIndex(
            [],
            vector_store=vector_store,
        )

        # Initialize HTML content
        html_content = []

        # Process each file
        success = True
        for file_path in files_to_process:
            file_success = process_file(file_path, index, model_name, ollama_url, output_dir, html_content)
            success = success and file_success

        # Generate and save the HTML report
        if success and html_content:
            report_title = f"SovereignRag - Security Analysis Report - {os.path.basename(path)}"
            html_report = generate_html_report(report_title, html_content)

            # Save the HTML report
            report_path = os.path.join(output_dir, "report.html")
            with open(report_path, "w") as f:
                f.write(html_report)

            print(f"{Fore.GREEN}{Style.BRIGHT}Report saved to: {report_path}")

        return success

    except Exception as e:
        print(f"{Fore.RED}{Style.BRIGHT}Error: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Analyze code for security vulnerabilities")
    parser.add_argument(
        "--path",
        "-p",
        "--file",
        "-f",
        dest="path",
        type=str,
        required=True,
        help="Path to the source code file or directory to analyze",
    )
    parser.add_argument(
        "--extension",
        "-e",
        type=str,
        help="File extension to filter by when path is a directory (e.g., 'py', 'java')",
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default="mistral:7b-instruct",
        help="Ollama model to use (default: mistral:7b-instruct)",
    )
    parser.add_argument(
        "--ollama-url",
        type=str,
        default="http://localhost:11434",
        help="Ollama API URL",
    )
    parser.add_argument(
        "--num-ctx",
        type=int,
        default=None,
        help=(
            "Ollama context window size (e.g. 4096, 8192). Lower values use less VRAM so the model fits on "
            "the GPU; omit to use the model default."
        ),
    )
    parser.add_argument(
        "--changed-only",
        action="store_true",
        help="Only analyze files changed in Git. By default this compares the working tree to --changed-base.",
    )
    parser.add_argument(
        "--changed-base",
        default="HEAD",
        help="Git ref used by --changed-only when --staged is not set (default: HEAD).",
    )
    parser.add_argument(
        "--staged",
        action="store_true",
        help="Only analyze staged files. Intended for pre-commit hooks.",
    )
    args = parser.parse_args()

    # If path is a directory, extension is required
    if os.path.isdir(args.path) and not args.extension:
        parser.error("--extension is required when path is a directory")

    success = run_query(
        args.path,
        args.extension,
        args.model,
        args.ollama_url,
        args.num_ctx,
        changed_only=args.changed_only,
        changed_base=args.changed_base,
        staged=args.staged,
    )
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
