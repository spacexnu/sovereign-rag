import fitz
import re
import spacy
from tqdm import tqdm
import os
import sys
import argparse
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)


def clean_text(text):
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'[ ]{2,}', ' ', text)
    text = re.sub(r'Page \d+ of \d+', '', text)
    text = text.strip()
    return text


def is_relevant_sentence(sent):
    if len(sent.text.strip()) < 20:
        return False
    if not any(tok.pos_ == 'VERB' for tok in sent):
        return False
    return True


def build_chunks_from_sentences(sentences: List[str], chunk_size_chars: int = 1800, overlap_sents: int = 2) -> List[str]:
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

    chunks: List[str] = []
    current: List[str] = []
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
    deduped: List[str] = []
    for c in chunks:
        if c not in seen:
            seen.add(c)
            deduped.append(c)

    return deduped


def preprocess_pdf(pdf_path, chunk_size_chars: int = 1800, overlap_sents: int = 2):
    try:
        doc = fitz.open(pdf_path)
        sentences: List[str] = []

        for page in tqdm(doc, desc=f'Processing {pdf_path}'):
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
        print(f'{Fore.RED}Error processing PDF {pdf_path}: {str(e)}')
        return []


def index_documents(pdf_dir, chunk_size_chars: int = 1800, overlap_sents: int = 2, embed_batch_size: int = 32):
    # Create directory if it doesn't exist
    if not os.path.exists(pdf_dir):
        print(f'{Fore.YELLOW}Creating directory {pdf_dir}')
        os.makedirs(pdf_dir)
        print(f'{Fore.YELLOW}Please add PDF files to {pdf_dir} and run the script again.')
        return

    # Check if directory contains PDF files
    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print(f'{Fore.YELLOW}No PDF files found in {pdf_dir}. Please add PDF files and run the script again.')
        return

    # Process each PDF file
    for file in pdf_files:
        file_path = os.path.join(pdf_dir, file)
        print(f'{Fore.CYAN}Processing {file_path}')
        chunks = preprocess_pdf(file_path, chunk_size_chars=chunk_size_chars, overlap_sents=overlap_sents)

        if not chunks:
            print(f'{Fore.YELLOW}No valid chunks extracted from {file_path}')
            continue

        print(f'{Fore.CYAN}Adding {len(chunks)} chunks to the vector database')
        try:
            embeddings = model.encode(chunks, batch_size=embed_batch_size, show_progress_bar=False)
        except Exception as e:
            print(f'{Fore.RED}Error encoding embeddings for {file_path}: {str(e)}')
            continue

        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            try:
                doc_id = f'{file}_{idx}'
                collection.add(documents=[chunk], embeddings=[embedding], ids=[doc_id])
            except Exception as e:
                print(f'{Fore.RED}Error adding chunk {idx} from {file_path}: {str(e)}')

    print(f'{Fore.GREEN}{Style.BRIGHT}Indexing completed!')


def run_ingest(pdf_dir='./sources/', model_name='all-MiniLM-L6-v2', chunk_size_chars: int = 1800, overlap_sents: int = 2, embed_batch_size: int = 32):
    """
    Run the ingestion process to index PDF documents.

    Args:
        pdf_dir (str): Directory containing PDF files to index
        model_name (str): Sentence transformer model to use
    """
    try:
        # Initialize spaCy
        global nlp
        nlp = spacy.load('en_core_web_sm')

        # Initialize sentence transformer
        global model
        model = SentenceTransformer(model_name)

        # Initialize ChromaDB
        global chroma_client, collection
        chroma_client = chromadb.PersistentClient(path='./chroma_db')
        collection = chroma_client.get_or_create_collection('security_docs')

        # Index documents
        index_documents(pdf_dir, chunk_size_chars=chunk_size_chars, overlap_sents=overlap_sents, embed_batch_size=embed_batch_size)

        return True

    except Exception as e:
        print(f'{Fore.RED}{Style.BRIGHT}Error: {str(e)}')
        return False


def main():
    """Command line interface for the ingest module."""
    parser = argparse.ArgumentParser(description='Index PDF documents for security analysis')
    parser.add_argument(
        '--pdf-dir',
        type=str,
        default='./raw_pdfs/',
        help='Directory containing PDF files to index (default: ./raw_pdfs/)',
    )
    parser.add_argument(
        '--model',
        type=str,
        default='all-MiniLM-L6-v2',
        help='Sentence transformer model to use (default: all-MiniLM-L6-v2)',
    )
    parser.add_argument(
        '--chunk-size-chars',
        type=int,
        default=1800,
        help='Target chunk size in characters (default: 1800)',
    )
    parser.add_argument(
        '--overlap-sents',
        type=int,
        default=2,
        help='Number of sentences to overlap between chunks (default: 2)',
    )
    parser.add_argument(
        '--embed-batch-size',
        type=int,
        default=32,
        help='Batch size for embedding encoding (default: 32)',
    )
    args = parser.parse_args()

    success = run_ingest(
        args.pdf_dir,
        args.model,
        chunk_size_chars=args.chunk_size_chars,
        overlap_sents=args.overlap_sents,
        embed_batch_size=args.embed_batch_size,
    )
    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()
