#!/usr/bin/env python3

import json
import os
import sys
import time
from pathlib import Path

import requests
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaLLM
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

sys.path.append("..")
from src.client import CheckerCallbackHandler


def main():
    required_env_vars = ["LANGFUSE_SECRET_KEY", "LANGFUSE_PUBLIC_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        print(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
        return

    DATA_DIR = Path("data")
    VECTOR_DB_DIR = Path("vector_db")
    DATA_DIR.mkdir(exist_ok=True)
    VECTOR_DB_DIR.mkdir(exist_ok=True)

    cat_facts_file = DATA_DIR / "cat-facts.txt"

    if not cat_facts_file.exists():
        try:
            response = requests.get(
                "https://huggingface.co/ngxson/demo_simple_rag_py/raw/main/cat-facts.txt",
                timeout=10,
            )
            response.raise_for_status()

            with open(cat_facts_file, "w", encoding="utf-8") as f:
                f.write(response.text)
        except Exception as e:
            print(f"Failed to download cat facts: {e}")
            return

    try:
        with open(cat_facts_file, "r", encoding="utf-8") as f:
            content = f.read().strip()

        documents = [
            fact.strip() for fact in content.split("\n") if fact.strip()
        ]

    except Exception as e:
        print(f"Failed to load cat facts: {e}")
        return

    langfuse = Langfuse(
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
    )
    langfuse_handler = CallbackHandler()
    mlchecker_handler = CheckerCallbackHandler()

    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    llm = OllamaLLM(
        model="mistral:7b",
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
    )

    doc_chunks = []
    for i, doc_text in enumerate(documents):
        chunks = text_splitter.split_text(doc_text)
        for j, chunk in enumerate(chunks):
            doc_chunks.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "doc_id": i,
                        "chunk_id": j,
                        "source": f"document_{i}",
                    },
                )
            )

    vectorstore_path = str(VECTOR_DB_DIR)

    if (VECTOR_DB_DIR / "chroma.sqlite3").exists():
        vectorstore = Chroma(
            persist_directory=vectorstore_path, embedding_function=embeddings
        )
    else:
        vectorstore = Chroma.from_documents(
            documents=doc_chunks,
            embedding=embeddings,
            persist_directory=vectorstore_path,
        )
        vectorstore.persist()

    prompt_template = ChatPromptTemplate.from_template("""
    You are a helpful assistant that answers questions based on the provided context.
    Use the context below to answer the user's question. If the context doesn't contain
    enough information to answer the question, say so honestly.

    Context:
    {context}

    Question: {question}

    Answer:
    """)

    print("\n🐱 Cat Facts RAG Chatbot with Langfuse Integration")
    print("=" * 50)
    print("Ask me anything about cats!")
    print("Type 'quit', 'exit', or 'bye' to end the session.\n")

    while True:
        try:
            user_input = input("\n💬 You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "bye"]:
                print("\n👋 Goodbye!")
                break

            context_docs = vectorstore.similarity_search(user_input, k=3)
            print(f"found context: {context_docs}")
            context = "\n\n".join([doc.page_content for doc in context_docs])

            prompt = prompt_template.format(
                context=context, question=user_input
            )
            response = llm.invoke(
                prompt,
                config={"callbacks": [langfuse_handler, mlchecker_handler]},
            )

            print(f"\n🤖 Bot: {response}")

        except KeyboardInterrupt:
            print("\n\n👋 Session interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            continue


if __name__ == "__main__":
    main()
