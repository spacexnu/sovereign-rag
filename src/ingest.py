import fitz
import re
import spacy
from tqdm import tqdm
import os
import sys
import argparse
import chromadb
from sentence_transformers import SentenceTransformer
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


def preprocess_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        all_chunks = []

        for page in tqdm(doc, desc=f'Processing {pdf_path}'):
            raw_text = page.get_text()
            cleaned = clean_text(raw_text)
            spacy_doc = nlp(cleaned)
            for sent in spacy_doc.sents:
                if is_relevant_sentence(sent):
                    all_chunks.append(sent.text.strip())

        return all_chunks
    except Exception as e:
        print(f'{Fore.RED}Error processing PDF {pdf_path}: {str(e)}')
        return []


def index_documents(pdf_dir):
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
        chunks = preprocess_pdf(file_path)

        if not chunks:
            print(f'{Fore.YELLOW}No valid chunks extracted from {file_path}')
            continue

        print(f'{Fore.CYAN}Adding {len(chunks)} chunks to the vector database')
        for idx, chunk in enumerate(chunks):
            try:
                embedding = model.encode(chunk)
                doc_id = f'{file}_{idx}'
                collection.add(documents=[chunk], embeddings=[embedding], ids=[doc_id])
            except Exception as e:
                print(f'{Fore.RED}Error adding chunk {idx} from {file_path}: {str(e)}')

    print(f'{Fore.GREEN}{Style.BRIGHT}Indexing completed!')


def run_ingest(pdf_dir='./sources/', model_name='all-MiniLM-L6-v2'):
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
        index_documents(pdf_dir)

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
    args = parser.parse_args()

    success = run_ingest(args.pdf_dir, args.model)
    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()
