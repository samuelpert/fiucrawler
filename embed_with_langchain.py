import os
import requests
from dotenv import load_dotenv
import numpy as np

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.base import Embeddings
from langchain_community.vectorstores import Qdrant

class OllamaMatryoshkaEmbeddings(Embeddings):
    """
    Ollama embeddings with Matryoshka truncation support.
    Nomic-embed-text v1.5 supports Matryoshka embeddings, allowing truncation
    to powers of 2 (512, 256, 128, 64) without retraining.
    """
    def __init__(self, 
                 model: str = "nomic-embed-text:v1.5", 
                 url: str = "http://localhost:11434/api/embeddings",
                 target_dim: int = 512):
        self.model = model
        self.url = url
        self.target_dim = target_dim
        
        # Validate target dimension for Matryoshka
        valid_dims = [64, 128, 256, 512, 768]
        if target_dim not in valid_dims:
            raise ValueError(f"Target dimension must be one of {valid_dims} for Matryoshka embeddings")

    def embed_documents(self, texts):
        return [self._embed(text) for text in texts]

    def embed_query(self, text):
        return self._embed(text)

    def _embed(self, text):
        # First, try with dimensionality parameter
        response = requests.post(
            self.url, 
            json={
                "model": self.model, 
                "prompt": text,
                "dimensionality": self.target_dim  # Try the parameter
            }
        )
        response.raise_for_status()
        embedding = response.json()["embedding"]
        
        # If we got the requested dimension, return it
        if len(embedding) == self.target_dim:
            return embedding
        
        # Otherwise, use Matryoshka truncation
        # This is mathematically valid for nomic-embed-text v1.5
        embedding_array = np.array(embedding[:self.target_dim])
        
        # Optional: Re-normalize after truncation (recommended for Matryoshka)
        norm = np.linalg.norm(embedding_array)
        if norm > 0:
            embedding_array = embedding_array / norm
            
        return embedding_array.tolist()

# Load environment variables
load_dotenv()

print("🚀 Starting embedding process with 512D Matryoshka embeddings...\n")

# Load documents
loader = DirectoryLoader(
    "fiu_content",
    glob="**/*.md",
    loader_cls=TextLoader,
    loader_kwargs={"encoding": "utf-8"},
    recursive=True
)
docs = loader.load()
print(f"📄 Loaded {len(docs)} documents")

# Split documents
splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
chunks = splitter.split_documents(docs)
print(f"✂️ Split into {len(chunks)} chunks")

# Create embeddings instance with 512D target
embeddings = OllamaMatryoshkaEmbeddings(target_dim=512)

# Test the embedding dimension
print("\n🧪 Testing embedding dimensions...")
test_embedding = embeddings.embed_query("Test query for dimension check")
print(f"✅ Embedding dimension: {len(test_embedding)}")

# Create Qdrant collection
print(f"\n📤 Uploading to Qdrant...")
try:
    vectorstore = Qdrant.from_documents(
        documents=chunks,
        embedding=embeddings,
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
        collection_name="fiu_content_v1_5_512d",  # Clear naming
        distance_func="Cosine",
        force_recreate=True,
        batch_size=100,  # Reasonable batch size
        content_payload_key="content",
        metadata_payload_key="metadata",
    )
    print("✅ All chunks embedded and uploaded to Qdrant collection 'fiu_content_v1_5_512d'")
    
    # Verify collection
    from qdrant_client import QdrantClient
    client = QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY")
    )
    collection_info = client.get_collection("fiu_content_v1_5_512d")
    print(f"\n📊 Collection info:")
    print(f"  - Vectors count: {collection_info.vectors_count}")
    print(f"  - Vector dimension: {collection_info.config.params.vectors.size}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Check your .env file has correct QDRANT_URL and QDRANT_API_KEY")
    print("2. Verify your Qdrant instance is running and accessible")
    print("3. Try reducing batch_size if you're getting timeout errors")