from rag.documents import process_document

if __name__ == "__main__":
    file_path = "data/22365_3_Prompt-Engineering_v7-1.pdf"
    chunks = process_document(file_path)
    print(f"✅ Processed {len(chunks)} chunks")
    print(chunks[0]["text"][:200])  # preview first chunk
