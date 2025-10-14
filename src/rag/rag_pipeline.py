# test_real_pipeline.py
from rag.documents import process_document
from rag.embeddings import embed_document_chunks , EmbeddingGenerator
from rag.vectorstore import store_embedded_documents ,search_documents

print("📄 Processing your PDF...")
chunks = process_document("data/22365_3_Prompt-Engineering_v7-1.pdf")

print("🔢 Generating embeddings...")  
embedded_chunks = embed_document_chunks(chunks)

print("📤 Storing in Pinecone...")
success = store_embedded_documents(embedded_chunks)
embeder = EmbeddingGenerator()

print((f"Converting query into embedding..."))
query = "What is prompt engineering?"
query_embedding = embeder.embed_single_text(query)


print(f"print query  embedding with embed_single_text:{query_embedding[:20]}")
query_embedding_list = query_embedding.tolist()
print("🔍 Testing search_documents with query embedding ...")
results = search_documents(query_embedding_list ,top_k =5)
print(f"Search results:{results}")

print(f"✅ Found {len(results)} relevant documents:")
for i, result in enumerate(results[:3]):
  print(f"\n{i+1}. Score: {result['score']:.3f}")
  print(f"   Text: {result['metadata']['text'][:150]}...")