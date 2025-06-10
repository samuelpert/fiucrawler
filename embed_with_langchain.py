import os
import re
import yaml
import requests
from dotenv import load_dotenv
import numpy as np

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.base import Embeddings
from langchain_community.vectorstores import Qdrant
from langchain.schema import Document

class MarkdownWithMetadataLoader(TextLoader):
    """Custom loader that extracts YAML frontmatter from markdown files"""
    
    def lazy_load(self):
        """Load and parse markdown file with YAML frontmatter"""
        with open(self.file_path, encoding=self.encoding) as f:
            content = f.read()
            
        # Extract YAML frontmatter - FIXED REGEX
        metadata = {}
        yaml_match = re.match(r'^---\n(.*?)\n---\n(.*)$', content, re.DOTALL)
        
        if yaml_match:
            try:
                # Parse YAML frontmatter
                yaml_content = yaml_match.group(1)
                metadata = yaml.safe_load(yaml_content) or {}
                
                # Get the content without frontmatter
                text_content = yaml_match.group(2).strip()
            except yaml.YAMLError as e:
                # If YAML parsing fails, try to extract metadata manually
                print(f"Error parsing YAML in {self.file_path}: {e}")
                
                # Try manual extraction as fallback
                metadata = self._extract_metadata_manually(yaml_content)
                text_content = yaml_match.group(2).strip()
        else:
            text_content = content
        
        # Add file information to metadata
        metadata['source'] = str(self.file_path)
        metadata['filename'] = os.path.basename(self.file_path)
        
        # Ensure all expected fields exist
        metadata.setdefault('url', 'Unknown URL')
        metadata.setdefault('site', 'Unknown Site')
        metadata.setdefault('crawled_at', 'Unknown Date')
        metadata.setdefault('title', 'Untitled')
        
        yield Document(
            page_content=text_content,
            metadata=metadata
        )
    
    def _extract_metadata_manually(self, yaml_content):
        """Manually extract metadata when YAML parsing fails"""
        metadata = {}
        lines = yaml_content.strip().split('\n')
        
        for line in lines:
            if ':' in line:
                # Split only on the first colon to handle colons in values
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                metadata[key] = value
        
        return metadata

class OllamaMatryoshkaEmbeddings(Embeddings):
    """
    Ollama embeddings with Matryoshka truncation support.
    """
    def __init__(self, 
                 model: str = "nomic-embed-text:v1.5", 
                 url: str = "http://localhost:11434/api/embeddings",
                 target_dim: int = 512):
        self.model = model
        self.url = url
        self.target_dim = target_dim
        
        valid_dims = [64, 128, 256, 512, 768]
        if target_dim not in valid_dims:
            raise ValueError(f"Target dimension must be one of {valid_dims} for Matryoshka embeddings")

    def embed_documents(self, texts):
        return [self._embed(text) for text in texts]

    def embed_query(self, text):
        return self._embed(text)

    def _embed(self, text):
        response = requests.post(
            self.url, 
            json={
                "model": self.model, 
                "prompt": text,
                "dimensionality": self.target_dim
            }
        )
        response.raise_for_status()
        embedding = response.json()["embedding"]
        
        if len(embedding) == self.target_dim:
            return embedding
        
        # Matryoshka truncation with normalization
        embedding_array = np.array(embedding[:self.target_dim])
        norm = np.linalg.norm(embedding_array)
        if norm > 0:
            embedding_array = embedding_array / norm
            
        return embedding_array.tolist()

# Load environment variables
load_dotenv()

print("🚀 Starting embedding process with metadata extraction...\n")

# Load documents with custom loader
loader = DirectoryLoader(
    "fiu_content2",
    glob="**/*.md",
    loader_cls=MarkdownWithMetadataLoader,  # Use our custom loader
    recursive=True
)
docs = loader.load()
print(f"📄 Loaded {len(docs)} documents")

# Count successful metadata extractions
successful_metadata = sum(1 for doc in docs if doc.metadata.get('url') != 'Unknown URL')
print(f"✅ Successfully parsed metadata for {successful_metadata}/{len(docs)} documents")

# Display sample metadata
if docs:
    print(f"\n📋 Sample document metadata:")
    sample_metadata = docs[0].metadata
    for key, value in sample_metadata.items():
        print(f"  - {key}: {value}")

# Split documents while preserving metadata
print(f"\n✂️ Splitting documents...")
splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000, 
    chunk_overlap=200,
    length_function=len,
)

# Split documents and ensure metadata is preserved
chunks = []
for doc in docs:
    doc_chunks = splitter.split_documents([doc])
    # Ensure each chunk has the parent document's metadata
    for chunk in doc_chunks:
        chunk.metadata = doc.metadata.copy()
        # Add chunk-specific metadata
        chunk.metadata['chunk_index'] = doc_chunks.index(chunk)
        chunk.metadata['total_chunks'] = len(doc_chunks)
        chunks.append(chunk)

print(f"✅ Split into {len(chunks)} chunks")

# Display sample chunk metadata
if chunks:
    print(f"\n📋 Sample chunk metadata:")
    sample_chunk_metadata = chunks[0].metadata
    for key, value in sample_chunk_metadata.items():
        print(f"  - {key}: {value}")

# Create embeddings instance
embeddings = OllamaMatryoshkaEmbeddings(target_dim=512)

# Test embedding
print("\n🧪 Testing embedding dimensions...")
test_embedding = embeddings.embed_query("Test query")
print(f"✅ Embedding dimension: {len(test_embedding)}")

# Create Qdrant collection with metadata
print(f"\n📤 Uploading to Qdrant with metadata...")
try:
    vectorstore = Qdrant.from_documents(
        documents=chunks,
        embedding=embeddings,
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
        collection_name="fiu_content",
        distance_func="Cosine",
        force_recreate=True,
        batch_size=100,
        content_payload_key="content",  # Changed to match LangChain default
        metadata_payload_key="metadata",
    )
    print("✅ All chunks embedded and uploaded with metadata!")
    
    # Verify by doing a test query
    print("\n🔍 Testing retrieval with metadata...")
    test_results = vectorstore.similarity_search_with_score(
        "student access success", 
        k=3
    )
    
    print(f"\n📊 Sample search results:")
    for i, (doc, score) in enumerate(test_results):
        print(f"\nResult {i+1} (score: {score:.4f}):")
        print(f"  URL: {doc.metadata.get('url', 'N/A')}")
        print(f"  Site: {doc.metadata.get('site', 'N/A')}")
        print(f"  Title: {doc.metadata.get('title', 'N/A')}")
        print(f"  Crawled: {doc.metadata.get('crawled_at', 'N/A')}")
        print(f"  Content preview: {doc.page_content[:100]}...")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ Done! Your Qdrant collection now includes all metadata from the markdown files.")
print("\n💡 When querying, you can access metadata fields like:")
print("  - doc.metadata['url'] - The original webpage URL")
print("  - doc.metadata['site'] - The site name")
print("  - doc.metadata['crawled_at'] - When it was crawled")
print("  - doc.metadata['title'] - The page title")
print("  - doc.metadata['filename'] - The markdown filename")
print("  - doc.metadata['chunk_index'] - Which chunk of the document")