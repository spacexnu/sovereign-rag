import argparse
import os
import re
import sys

import chromadb
import fitz
import spacy
from colorama import Fore, Style, init
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Initialize colorama
init(autoreset=True)


def clean_text(text):
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r"Page \d+ of \d+", "", text)
    text = text.strip()
    return text


def is_relevant_sentence(sent):
    """Decide whether a spaCy sentence carries enough signal to index.

    OWASP and similar security references rely heavily on verb-less lines:
    vulnerability names ("Broken Access Control"), control titles, and checklist
    items. A strict "must contain a VERB" rule would drop most of that, so
    verb-less lines are kept when they hold enough nouns to be a real technical
    phrase rather than a page header or stray fragment.
    """
    text = sent.text.strip()

    # Drop tiny fragments (page numbers, stray tokens, list bullets).
    if len(text) < 12:
        return False

    # Need at least two real words; filters out things like "5 -" or "•".
    content_tokens = [tok for tok in sent if tok.is_alpha]
    if len(content_tokens) < 2:
        return False

    # Prose: a verb signals a full sentence — always relevant.
    if any(tok.pos_ == "VERB" for tok in sent):
        return True

    # Verb-less line: keep it only if it reads like a meaningful technical
    # phrase (e.g. a vulnerability name or control title) rather than noise.
    noun_like = sum(1 for tok in sent if tok.pos_ in ("NOUN", "PROPN"))
    return noun_like >= 2


def build_chunks_from_sentences(
    sentences: list[str], chunk_size_chars: int = 1800, overlap_sents: int = 2
) -> list[str]:
    """Group sentences into larger chunks to control context size.

    Args:
        sentences: List of sentence strings.
        chunk_size_chars: Target chunk size in characters.
        overlap_sents: Number of sentences to overlap between consecutive chunks.

    Returns:
        List of chunk strings.
    """
    if not sentences:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for s in sentences:
        s = s.strip()
        if not s:
            continue
        # +1 for space/newline join
        projected = current_len + len(s) + (1 if current else 0)

        if current and projected > chunk_size_chars:
            chunk = " ".join(current).strip()
            if chunk:
                chunks.append(chunk)

            # overlap: keep last N sentences
            if overlap_sents > 0:
                current = current[-overlap_sents:]
                current_len = sum(len(x) for x in current) + max(0, len(current) - 1)
            else:
                current = []
                current_len = 0

        current.append(s)
        current_len = current_len + len(s) + (1 if len(current) > 1 else 0)

    # flush
    final_chunk = " ".join(current).strip()
    if final_chunk:
        chunks.append(final_chunk)

    # de-duplicate while preserving order
    seen = set()
    deduped: list[str] = []
    for c in chunks:
        if c not in seen:
            seen.add(c)
            deduped.append(c)

    return deduped


def strip_markdown(text: str) -> str:
    """Reduce Markdown markup to plain prose before spaCy segmentation.

    Most OWASP docs ship as Markdown: stripping fences, headings, links and
    emphasis markers keeps spaCy from treating syntax tokens (``#``, ``*``,
    ``[]()``) as part of the technical phrases we want to index.
    """
    # Drop fenced code blocks entirely.
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    # Inline code: keep the contents, drop the backticks.
    text = re.sub(r"`([^`]*)`", r"\1", text)
    # Images and links: keep the visible text, drop the target.
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    # Heading, blockquote and list markers at line start.
    text = re.sub(r"(?m)^\s{0,3}(#{1,6}|>|[-*+]|\d+\.)\s+", "", text)
    # Emphasis / bold markers.
    text = re.sub(r"[*_~]{1,3}", "", text)
    return text


def _chunk_sentences(text: str, chunk_size_chars: int, overlap_sents: int) -> list[str]:
    """Run spaCy segmentation + relevance filtering, then group into chunks."""
    sentences: list[str] = []
    spacy_doc = nlp(text)
    for sent in spacy_doc.sents:
        if is_relevant_sentence(sent):
            sentences.append(sent.text.strip())
    return build_chunks_from_sentences(sentences, chunk_size_chars=chunk_size_chars, overlap_sents=overlap_sents)


def preprocess_pdf(pdf_path, chunk_size_chars: int = 1800, overlap_sents: int = 2):
    try:
        doc = fitz.open(pdf_path)
        sentences: list[str] = []

        for page in tqdm(doc, desc=f"Processing {pdf_path}"):
            raw_text = page.get_text()
            cleaned = clean_text(raw_text)
            if not cleaned:
                continue
            spacy_doc = nlp(cleaned)
            for sent in spacy_doc.sents:
                if is_relevant_sentence(sent):
                    sentences.append(sent.text.strip())

        # Group sentences into larger chunks (fewer, bigger chunks = faster LLM context)
        return build_chunks_from_sentences(sentences, chunk_size_chars=chunk_size_chars, overlap_sents=overlap_sents)

    except Exception as e:
        print(f"{Fore.RED}Error processing PDF {pdf_path}: {str(e)}")
        return []


def preprocess_markdown(md_path, chunk_size_chars: int = 1800, overlap_sents: int = 2):
    try:
        with open(md_path, encoding="utf-8") as f:
            raw_text = f.read()

        cleaned = clean_text(strip_markdown(raw_text))
        if not cleaned:
            return []

        return _chunk_sentences(cleaned, chunk_size_chars, overlap_sents)

    except Exception as e:
        print(f"{Fore.RED}Error processing Markdown {md_path}: {str(e)}")
        return []


def find_source_files(docs_dir: str) -> list[str]:
    """Return supported source files under docs_dir, recursively and deterministically."""
    source_files: list[str] = []
    for root, dirs, files in os.walk(docs_dir):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        for file in sorted(files):
            if file.lower().endswith((".pdf", ".md")):
                source_files.append(os.path.join(root, file))
    return source_files


def index_documents(docs_dir, chunk_size_chars: int = 1800, overlap_sents: int = 2, embed_batch_size: int = 32):
    # Create directory if it doesn't exist
    if not os.path.exists(docs_dir):
        print(f"{Fore.YELLOW}Creating directory {docs_dir}")
        os.makedirs(docs_dir)
        print(f"{Fore.YELLOW}Please add .pdf/.md files to {docs_dir} and run the script again.")
        return

    # Check if directory contains supported files (PDF and Markdown), recursively.
    source_files = find_source_files(docs_dir)
    if not source_files:
        print(
            f"{Fore.YELLOW}No PDF or Markdown files found in {docs_dir}. "
            "Please add .pdf/.md files and run the script again."
        )
        return

    # Process each source file, dispatching by extension
    for file_path in source_files:
        relative_path = os.path.relpath(file_path, docs_dir)
        print(f"{Fore.CYAN}Processing {file_path}")
        if file_path.lower().endswith(".md"):
            chunks = preprocess_markdown(file_path, chunk_size_chars=chunk_size_chars, overlap_sents=overlap_sents)
        else:
            chunks = preprocess_pdf(file_path, chunk_size_chars=chunk_size_chars, overlap_sents=overlap_sents)

        if not chunks:
            print(f"{Fore.YELLOW}No valid chunks extracted from {file_path}")
            continue

        print(f"{Fore.CYAN}Adding {len(chunks)} chunks to the vector database")
        for idx, chunk in enumerate(chunks):
            try:
                embedding = model.encode(chunk, batch_size=embed_batch_size, show_progress_bar=False)
            except Exception as e:
                print(f"{Fore.RED}Error encoding embeddings for {file_path}: {str(e)}")
                continue

            try:
                doc_id = f"{relative_path}_{idx}"
                collection.add(
                    documents=[chunk],
                    embeddings=[embedding],
                    ids=[doc_id],
                    metadatas=[{"source": relative_path}],
                )
            except Exception as e:
                print(f"{Fore.RED}Error adding chunk {idx} from {file_path}: {str(e)}")

    print(f"{Fore.GREEN}{Style.BRIGHT}Indexing completed!")


def run_ingest(
    docs_dir="./sources/",
    model_name="all-MiniLM-L6-v2",
    chunk_size_chars: int = 1800,
    overlap_sents: int = 2,
    embed_batch_size: int = 32,
):
    """
    Run the ingestion process to index PDF/Markdown documents.

    Args:
        docs_dir (str): Directory containing .pdf/.md files to index
        model_name (str): Sentence transformer model to use
    """
    try:
        # Initialize spaCy
        global nlp
        nlp = spacy.load("en_core_web_sm")

        # Initialize sentence transformer
        global model
        model = SentenceTransformer(model_name)

        # Initialize ChromaDB
        global chroma_client, collection
        chroma_client = chromadb.PersistentClient(path="./chroma_db")
        collection = chroma_client.get_or_create_collection("security_docs")

        # Index documents
        if chunk_size_chars == 1800 and overlap_sents == 2 and embed_batch_size == 32:
            index_documents(docs_dir)
        else:
            index_documents(
                docs_dir,
                chunk_size_chars=chunk_size_chars,
                overlap_sents=overlap_sents,
                embed_batch_size=embed_batch_size,
            )

        return True

    except Exception as e:
        print(f"{Fore.RED}{Style.BRIGHT}Error: {str(e)}")
        return False


def main():
    """Command line interface for the ingest module."""
    parser = argparse.ArgumentParser(description="Index PDF/Markdown documents for security analysis")
    parser.add_argument(
        "--docs-dir",
        "--pdf-dir",
        dest="docs_dir",
        type=str,
        default="./raw_pdfs/",
        help="Directory containing .pdf/.md files to index (default: ./raw_pdfs/). "
        "--pdf-dir is a deprecated alias.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="all-MiniLM-L6-v2",
        help="Sentence transformer model to use (default: all-MiniLM-L6-v2)",
    )
    parser.add_argument(
        "--chunk-size-chars",
        type=int,
        default=1800,
        help="Target chunk size in characters (default: 1800)",
    )
    parser.add_argument(
        "--overlap-sents",
        type=int,
        default=2,
        help="Number of sentences to overlap between chunks (default: 2)",
    )
    parser.add_argument(
        "--embed-batch-size",
        type=int,
        default=32,
        help="Batch size for embedding encoding (default: 32)",
    )
    args = parser.parse_args()

    success = run_ingest(
        args.docs_dir,
        args.model,
        chunk_size_chars=args.chunk_size_chars,
        overlap_sents=args.overlap_sents,
        embed_batch_size=args.embed_batch_size,
    )
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
