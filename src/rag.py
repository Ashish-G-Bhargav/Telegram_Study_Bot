import pymupdf4llm
import chromadb
from chromadb.utils import embedding_functions
import os
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path

def pdf_2_md(path, sub_code):
    try:
        md_file = pymupdf4llm.to_markdown(path, page_chunks=True)
    except Exception as e:
        print(f"Error processing PDF {path}: {e}")
        return None

    pdf_filename = os.path.basename(path)

    text = []
    metadata = []
    ids = []

    for i, chunk in enumerate(md_file):
        text.append(chunk["text"])

        chunk_metadata = chunk.get("metadata", {})
        clean_metadata = {
            "source": pdf_filename,
            "page_number": chunk_metadata.get("page", -1) + 1,
            "type": chunk_metadata.get("type", "unknown")
        }
        metadata.append(clean_metadata)
        ids.append(f"{sub_code}_{pdf_filename}_chunk_{i}")

    return [text, metadata, ids]

def add_to_vdb(md_lst):
    db_path = "vector_db"
    embedding_model = "mixedbread-ai/mxbai-embed-large-v1"

    client = chromadb.PersistentClient(path=db_path)

    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=embedding_model, device="cuda")
    try:
        collection = client.get_or_create_collection(name="collage_notes_database", embedding_function=embedding_function)
        collection.upsert(documents=md_lst[0], ids=md_lst[2], metadatas=md_lst[1])
    except ValueError as e:
        print(f"Error: {e}")
        return

    print(f"Successfully added {len(md_lst[0])} chunks to the '{collection.name}' collection.")

def get_context(query):
    db_path = "vector_db"
    embedding_model = "mixedbread-ai/mxbai-embed-large-v1"

    client = chromadb.PersistentClient(path=db_path)

    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=embedding_model, device="cuda")

    try:
        collection = client.get_collection(
            name="collage_notes_database",
            embedding_function=embedding_function
        )
    except ValueError:
        print("Error: Collection collage_notes_database not found.")
        exit()

    results = collection.query(
        query_texts=[query],
        n_results=5
    )

    context = ""
    for doc in results["documents"][0]:
        context += f"\n{doc}\n\n"

    return context

def ask_llm(query):
    load_dotenv()
    api_key = os.getenv("OPEN_ROUTER_API")

    if not api_key:
        raise ValueError("OPEN_ROUTER_API environment variable is not set.")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    context = get_context(query)

    prompt = f"""You are a helpful Academic assistant that helps students to answer their queries based on the provided context from their study materials. Use the context to provide in depth explanation for the question. If the context does not contain the information needed to answer the question, respond with "I don't know".

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

    return response.choices[0].message.content.strip()

def add_to_db(sub_code):
    path = Path(f"notes/{sub_code}")
    if not path.exists() or not path.is_dir():
        print(f"Directory {path} does not exist.")
        return

    for file in path.glob("*.pdf"):
        print(f"Processing file: {file}")
        md = pdf_2_md(file, sub_code)
        if md:
            add_to_vdb(md)
        else:
            print(f"Skipping file {file} due to processing error.")