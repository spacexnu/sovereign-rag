import argparse
import os
import sys

from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)


def main():
    # Create the main parser
    parser = argparse.ArgumentParser(
        description=f"{Fore.CYAN}{Style.BRIGHT}Sovereign RAG - A tool for security analysis using RAG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Create the ingest command parser
    ingest_parser = subparsers.add_parser("ingest", help="Index PDF documents for security analysis")
    ingest_parser.add_argument(
        "--pdf-dir",
        type=str,
        default="./raw_pdfs/",
        help="Directory containing PDF files to index (default: ./raw_pdfs/)",
    )
    ingest_parser.add_argument(
        "--model",
        type=str,
        default="all-MiniLM-L6-v2",
        help="Sentence transformer model to use (default: all-MiniLM-L6-v2)",
    )
    ingest_parser.add_argument(
        "--chunk-size-chars",
        type=int,
        default=1800,
        help="Target chunk size in characters (default: 1800)",
    )
    ingest_parser.add_argument(
        "--overlap-sents",
        type=int,
        default=2,
        help="Number of sentences to overlap between chunks (default: 2)",
    )
    ingest_parser.add_argument(
        "--embed-batch-size",
        type=int,
        default=32,
        help="Batch size for embedding encoding (default: 32)",
    )

    # Create the query command parser
    query_parser = subparsers.add_parser("query", help="Analyze code for security vulnerabilities")
    query_parser.add_argument(
        "--path",
        "-p",
        type=str,
        required=True,
        help="Path to the source code file or directory to analyze",
    )
    query_parser.add_argument(
        "--extension",
        "-e",
        type=str,
        help="File extension to filter by when path is a directory (e.g., 'py', 'java')",
    )
    query_parser.add_argument(
        "--model",
        "-m",
        type=str,
        default="mistral:7b-instruct",
        help="Ollama model to use (default: mistral:7b-instruct)",
    )
    query_parser.add_argument(
        "--ollama-url",
        type=str,
        default="http://localhost:11434",
        help="Ollama API URL",
    )

    # Parse arguments
    args = parser.parse_args()

    # If no command is provided, show help
    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute the appropriate command
    print(f"\n{Fore.YELLOW}Wait...")
    if args.command == "ingest":
        from .ingest import run_ingest

        run_ingest(
            args.pdf_dir,
            args.model,
            chunk_size_chars=args.chunk_size_chars,
            overlap_sents=args.overlap_sents,
            embed_batch_size=args.embed_batch_size,
        )
    elif args.command == "query":
        from .query import run_query

        # If path is a directory, extension is required
        if os.path.isdir(args.path) and not args.extension:
            print(f"{Fore.RED}{Style.BRIGHT}Error: --extension is required when path is a directory")
            sys.exit(1)

        run_query(args.path, args.extension, args.model, args.ollama_url)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Operation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"{Fore.RED}{Style.BRIGHT}Error: {str(e)}")
        sys.exit(1)
