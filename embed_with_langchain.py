import os
import requests
from dotenv import load_dotenv

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter    import RecursiveCharacterTextSplitter
from langchain.embeddings.base  import Embeddings
from langchain_community.vectorstores import Qdrant

class OllamaEmbeddings(Embeddings):
    def __init__(self, model: str = "nomic-embed-text", url: str = "http://localhost:11434/api/embeddings", dimensions: int = 512):
        self.model = model
        self.url = url
        self.dimensions = dimensions

    def embed_documents(self, texts):
        return [self._embed(text) for text in texts]

    def embed_query(self, text):
        return self._embed(text)

    def _embed(self, text):
        response = requests.post(self.url, json={"model": self.model, "prompt": text})
        response.raise_for_status()
        return response.json()["embedding"]

load_dotenv()

loader = DirectoryLoader(
    "fiu_content",
    glob="**/*.md",
    loader_cls=TextLoader,
    loader_kwargs={"encoding": "utf-8"},
    recursive=True
)
docs = loader.load()
print(f"Loaded {len(docs)} documents")

splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
chunks   = splitter.split_documents(docs)
print(f"Split into {len(chunks)} chunks")

embeddings = OllamaEmbeddings()

vectorstore = Qdrant.from_documents(
    documents       = chunks,
    embedding       = embeddings,
    url             = os.getenv("QDRANT_URL"),
    api_key         = os.getenv("QDRANT_API_KEY"),
    collection_name = "fiu_content",
    distance_func   = "Cosine",
    force_recreate  = True,
    batch_size      = 400,
    content_payload_key="content",  # Custom key for document content
    metadata_payload_key="metadata",  # Custom key for document metadata
)

print("✅ All chunks embedded and uploaded to Qdrant collection 'fiu_content'")