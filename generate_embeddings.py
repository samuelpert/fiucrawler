import os
import torch 
from pathlib import Path
from sentence_transformers import SentenceTransformer
import re
import json
from datetime import datetime
import yaml
from qdrant_client import QdrantClient
from qdrant_client.http import models

from dotenv import load_dotenv


load_dotenv() 
 
# ======= SETTINGS ========
# Set which site folder to process (e.g. "parking", "admissions", etc.)
# This must match a folder name inside fiu_content directory
SITE_TO_PROCESS = "shop_fiu"  # <-- CHANGE THIS VALUE to the folder you want to process


 
print(f"Starting embeddings generation for site: {SITE_TO_PROCESS}")
 
# Initialize the model
model = SentenceTransformer('all-mpnet-base-v2')  # Stronger model with better semantic understanding
 
# Get embedding dimension
embedding_dimension = model.get_sentence_embedding_dimension()
print(f"Embedding dimension: {embedding_dimension}")

# Initialize Qdrant client
def get_qdrant_client():
    return QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))

# Create collection if it doesn't exist
def ensure_collection(client, collection_name, embedding_dimension):
    try:
        collection_info = client.get_collection(collection_name=collection_name)
        print(f"Collection '{collection_name}' already exists")
    except Exception:
        print(f"Creating collection '{collection_name}'")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=embedding_dimension,
                distance=models.Distance.COSINE
            )
        )
        
# Custom JSON encoder to handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)
 
# Function to extract text and metadata from markdown files
def extract_from_markdown(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
   
    # Extract YAML frontmatter
    metadata = {}
    frontmatter_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if frontmatter_match:
        frontmatter_text = frontmatter_match.group(1)
        try:
            metadata = yaml.safe_load(frontmatter_text)
        except Exception as e:
            print(f"Warning: Could not parse metadata in {file_path}: {str(e)}")
       
        # Remove the frontmatter from content
        content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)
   
    # Remove markdown formatting (basic cleanup)
    content = re.sub(r'#+ ', '', content)  # Remove headers
    content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)  # Replace links with link text
    content = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', content)  # Remove images
    content = re.sub(r'[*_]{1,2}([^*_]+)[*_]{1,2}', r'\1', content)  # Remove bold/italic
   
    return content.strip(), metadata
 
# Function to process a specific site
def process_site(site_name):
    fiu_content_dir = Path("fiu_content")
    site_path = os.path.join(fiu_content_dir, site_name)
   
    if not os.path.exists(site_path) or not os.path.isdir(site_path):
        print(f"Error: Site '{site_name}' not found in {fiu_content_dir}")
        print("Available sites:")
        for site_dir in os.listdir(fiu_content_dir):
            if os.path.isdir(os.path.join(fiu_content_dir, site_dir)):
                file_count = len([f for f in os.listdir(os.path.join(fiu_content_dir, site_dir)) if f.endswith('.md')])
                print(f"  - {site_dir} ({file_count} files)")
        return []
   
    documents = []
    metadata_list = []
    file_paths = []
   
    print(f"Processing site: {site_name}")
   
    # Get all markdown files in the site directory
    for file in os.listdir(site_path):
        if file.endswith('.md'):
            file_path = os.path.join(site_path, file)
            text, metadata = extract_from_markdown(file_path)
           
            # Skip very short or empty documents
            if len(text.split()) < 10:
                print(f"Skipping {file_path} (too short)")
                continue
           
            # Store document text, metadata, and file path
            documents.append(text)
            metadata_list.append(metadata)
            file_paths.append(file_path)
   
    # Generate embeddings for all documents
    if documents:
        print(f"Generating embeddings for {len(documents)} documents in {site_name}...")
        embeddings = model.encode(documents)
       
        # Create results
        results = []
        for i, (doc, embedding, metadata, file_path) in enumerate(zip(documents, embeddings, metadata_list, file_paths)):
            results.append({
                'id': i,
                'text': doc[:200] + '...' if len(doc) > 200 else doc,  # Preview
                'file_path': file_path,
                'metadata': metadata,
                'embedding': embedding.tolist()  # Convert numpy array to list for JSON serialization
            })
       
        # Create embeddings directory if it doesn't exist
        embeddings_dir = Path("embeddings")
        embeddings_dir.mkdir(exist_ok=True)
       
        # Save embeddings to file specific to this site
        output_path = embeddings_dir / f"{site_name}_embeddings.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)
       
        print(f"Saved {len(results)} embeddings to {output_path}")
        
        # Upload embeddings to Qdrant
        try:
            print(f"Uploading embeddings to Qdrant collection '{site_name}'...")
            client = get_qdrant_client()
            
            # Ensure collection exists
            ensure_collection(client, site_name, embedding_dimension)
            
            # Prepare points for upload
            points = []
            for result in results:
                points.append(
                    models.PointStruct(
                        id=result['id'],
                        vector=result['embedding'],
                        payload={
                            'text': result['text'],
                            'file_path': result['file_path'],
                            'metadata': result['metadata']
                        }
                    )
                )
            
            # Upsert points in batches of 100
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                client.upsert(
                    collection_name=site_name,
                    points=batch
                )
                print(f"Uploaded batch {i//batch_size + 1}/{(len(points) + batch_size - 1)//batch_size}")
            
            print(f"Successfully uploaded {len(points)} embeddings to Qdrant collection '{site_name}'")
        except Exception as e:
            print(f"Error uploading embeddings to Qdrant: {str(e)}")
        
        return results
    else:
        print(f"No suitable documents found in {site_name}")
        return []
 
if __name__ == "__main__":
    # Process the site specified in the SITE_TO_PROCESS variable
    process_site(SITE_TO_PROCESS)
 
 