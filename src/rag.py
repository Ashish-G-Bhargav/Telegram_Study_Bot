import pymupdf4llm
import os
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path
from langchain.text_splitter import MarkdownHeaderTextSplitter

from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_chroma import Chroma  
from langchain_huggingface import HuggingFaceEmbeddings  
from langchain_core.documents import Document

import pickle
import shutil

def pdf_2_md(path, sub_code):
    try:
        md = pymupdf4llm.to_markdown(path)
    except Exception as e:
        print(f"Error processing PDF {path}: {e}")
        return None

    pdf_filename = os.path.basename(path)
    headers_to_split_on = [("#", "Header 1"), ("##", "Header 2"), ("###", "Header 3")]
    text_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    md_file = text_splitter.split_text(md)

    documents = []
    
    for i, chunk in enumerate(md_file):
        doc = Document(
            page_content=chunk.page_content,  
            metadata={
                "source": pdf_filename,
                "page_number": chunk.metadata.get("page", -1) + 1,
                "type": chunk.metadata.get("type", "unknown"),
                "chunk_id": f"{sub_code}_{pdf_filename}_chunk_{i}",
                "subject_code": sub_code
            }
        )
        documents.append(doc)

    return documents


ensemble_retriever = None
bm25_retriever = None
vector_retriever = None
vector_store = None  
all_documents = []

def build_ensemble_retriever():
    global ensemble_retriever, bm25_retriever, vector_retriever, vector_store, all_documents
    
    if not all_documents:
        print("No documents found. Please add documents first.")
        return None
    
    print(f"Building ensemble retriever with {len(all_documents)} documents...")
    
    try:
        bm25_retriever = BM25Retriever.from_documents(
            all_documents,
            k=10
        )
        
        
        embeddings = HuggingFaceEmbeddings(
            model_name="mixedbread-ai/mxbai-embed-large-v1",
            model_kwargs={'device': 'cuda'}
        )
        
        vector_store = Chroma.from_documents(
            documents=all_documents,
            embedding=embeddings,  
            persist_directory="vector_db"
        )
        
        vector_retriever = vector_store.as_retriever(
            search_kwargs={"k": 10}
        )
        
        ensemble_retriever = EnsembleRetriever(
            retrievers=[bm25_retriever, vector_retriever],
            weights=[0.5, 0.5],  
            search_type="mmr"
        )
        
        print("Ensemble retriever built successfully!")
        return ensemble_retriever
        
    except Exception as e:
        print(f"Error building ensemble retriever: {e}")
        return None

def save_documents():
    
    global all_documents
    with open("all_documents.pkl", "wb") as f:
        pickle.dump(all_documents, f)
    print(f"Documents saved to disk: {len(all_documents)} documents")

def load_documents():
    global all_documents, vector_store
    try:
        with open("all_documents.pkl", "rb") as f:
            all_documents = pickle.load(f)
        print(f"Loaded {len(all_documents)} documents from disk")
        
        if Path("vector_db").exists():
           
            embeddings = HuggingFaceEmbeddings(
                model_name="mixedbread-ai/mxbai-embed-large-v1",
                model_kwargs={'device': 'cuda'}
            )
            
            vector_store = Chroma(
                persist_directory="vector_db",
                embedding_function=embeddings  
            )
            print("Vector store reloaded")
        
        return True
    except FileNotFoundError:
        print("No saved documents found")
        return False
    except Exception as e:
        print(f"Error loading documents: {e}")
        return False

def add_to_vdb(documents):
    
    global all_documents, ensemble_retriever, vector_store
    
   
    all_documents.extend(documents)
    
    
    if vector_store is not None:
        vector_store.add_documents(documents)
        print(f"Added {len(documents)} documents to existing vector store")
    
    
    save_documents()
    
    
    build_ensemble_retriever()
    
    print(f"Total documents in ensemble: {len(all_documents)}")

def get_context(query, use_ensemble=True):
    
    global ensemble_retriever, vector_store
    
    print(f" Getting context for: {query}")
    print(f" Ensemble retriever available: {ensemble_retriever is not None}")
    print(f" Vector store available: {vector_store is not None}")
    print(f" Total documents: {len(all_documents)}")
    
    if use_ensemble and ensemble_retriever:
        try:
            print("Trying ensemble retriever...")
            retrieved_docs = ensemble_retriever.get_relevant_documents(query)
            context = ""
           
            for doc in retrieved_docs:
                chunk = doc.page_content + "..." 
                context += f"\n{chunk}\n\n"
            
            print(f"Retrieved {len(retrieved_docs)} documents using ensemble retriever")
            return context
            
        except Exception as e:
            print(f" Error with ensemble retriever: {e}")
            print(" Falling back to vector store...")
    
   
    if vector_store:
        try:
            print(" Trying vector store...")
            docs = vector_store.similarity_search(query, k=10)
            context = ""
            for doc in docs:
                chunk = doc.page_content + "..." 
                context += f"\n{chunk}\n\n"
            
            print(f" Retrieved {len(docs)} documents using vector store fallback")
            return context
            
        except Exception as e:
            print(f" Error with vector store: {e}")
    
    print(" No retrieval method available")
    return ""

def ask_llm(query):
    load_dotenv()
    api_key = os.getenv("OPEN_ROUTER_API")

    if not api_key: 
        raise ValueError("OPEN_ROUTER_API environment variable is not set.")
    
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    
    context = get_context(query, use_ensemble=True)

    prompt = f"""You are a helpful Academic assistant in a RAG system  that helps students to answer their queries based on the provided context from their study materials. Use the context to provide in depth explanation for the question. If the context does not contain the information needed to answer the question, respond with "I don't know".
    
    Important: Provide the answer as plain text only, without any Markdown formatting (no asterisks, hashes, or dashes).
    
    
    Context:
    {context}

    Question:
    {query}

    Answer:
    """

    response = client.chat.completions.create(
        model="deepseek/deepseek-chat-v3.1:free",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    try:

        if response and response.choices:
                return response.choices[0].message.content.strip()
        else:
                # If the API gives an empty response, return this message
                return "The AI model returned an empty or invalid response. Please try rephrasing your question."
        
    except Exception as e:
        print(f"An error occurred in ask_llm: {e}")
        return f"An error occurred while communicating with the AI model: {str(e)}"

def add_to_db(sub_code):
    
    path = Path(f"notes/{sub_code}")
    if not path.exists() or not path.is_dir():
        print(f"Directory {path} does not exist.")
        return
    
    for file in path.glob("*.pdf"):
        print(f"Processing file: {file}")
        documents = pdf_2_md(file, sub_code)
        if documents:
            add_to_vdb(documents)
        else:
            print(f"Skipping file {file} due to processing error.")

def clear_all_vector_dbs():
    """Delete all vector databases and cached documents"""
    global ensemble_retriever, bm25_retriever, vector_retriever, vector_store, all_documents
    
    print("Clearing all vector databases...")
    
    
    ensemble_retriever = None
    bm25_retriever = None
    vector_retriever = None
    vector_store = None
    all_documents = []
    
    
    for db_path in ["vector_db", "vector_db_langchain"]:
        path = Path(db_path)
        if path.exists():
            try:
                shutil.rmtree(path)
                print(f"Deleted {db_path}")
            except Exception as e:
                print(f"Error deleting {db_path}: {e}")
    
    
    docs_cache = Path("all_documents.pkl")
    if docs_cache.exists():
        try:
            docs_cache.unlink()
            print("Deleted document cache")
        except Exception as e:
            print(f"Error deleting document cache: {e}")
    
    print("All vector databases cleared successfully!")

def recreate_vector_dbs_from_notes():
    """Recreate vector database from all existing PDF notes"""
    print("Recreating vector database from existing notes...")
    clear_all_vector_dbs()
    
    notes_path = Path("notes")
    if not notes_path.exists():
        print("No notes directory found")
        return False
    
    total_files = 0
    processed_files = 0
    
    for subject_dir in notes_path.iterdir():
        if subject_dir.is_dir():
            subject_code = subject_dir.name
            print(f"Processing subject: {subject_code}")
            
            pdf_files = list(subject_dir.glob("*.pdf"))
            total_files += len(pdf_files)
            
            for pdf_file in pdf_files:
                try:
                    print(f"   Processing: {pdf_file.name}")
                    documents = pdf_2_md(pdf_file, subject_code)
                    
                    if documents:
                        add_to_vdb(documents)
                        processed_files += 1
                        print(f"   Added {len(documents)} chunks from {pdf_file.name}")
                    else:
                        print(f"   Failed to process {pdf_file.name}")
                        
                except Exception as e:
                    print(f"   Error processing {pdf_file.name}: {e}")
    
    print(f"\nRecreation complete!")
    print(f"Processed {processed_files}/{total_files} PDF files")
    print(f"Total documents in database: {len(all_documents)}")
    
    return processed_files > 0


if load_documents():
    build_ensemble_retriever()
else:
    print("No existing documents found. Database will be built when documents are added.")

if __name__ == "__main__":
    print("Vector Database Management")
    print("1. Print current stats")
    print("2. Clear all databases")
    print("3. Recreate from notes")
    
    choice = input("\nEnter your choice (1-3): ")
    
    if choice == "1":
        print(f"Total documents: {len(all_documents)}")
        print(f"Ensemble active: {ensemble_retriever is not None}")
        print(f"Vector store active: {vector_store is not None}")
    elif choice == "2":
        clear_all_vector_dbs()
    elif choice == "3":
        recreate_vector_dbs_from_notes()
    else:
        print("Invalid choice")







