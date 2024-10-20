import os
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain.llms import HuggingFacePipeline
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline
import tempfile

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize language model
model_name = "google/flan-t5-base"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
llm = HuggingFacePipeline(pipeline=pipeline(
    "text2text-generation",
    model=model,
    tokenizer=tokenizer,
    max_length=512,
    temperature=0.3
))

# Initialize embeddings
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Initialize vector store
vectorstore = None

@app.get("/")
async def root():
    return {"message": "Welcome to the Document Chatter API"}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    global vectorstore
    
    print(f"Received file: {file.filename}, Size: {file.size} bytes")
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Load and process document
        loader = PyPDFLoader(temp_file_path)
        documents = loader.load()
        print(f"Loaded {len(documents)} pages from PDF")
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_documents(documents)
        print(f"Split into {len(texts)} text chunks")
        
        # Create vector store
        vectorstore = FAISS.from_documents(texts, embeddings)
        print("Vector store created successfully")
        
    except Exception as e:
        print(f"Error processing document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            print(f"Temporary file {temp_file_path} removed")
    
    return {"message": "Document uploaded and processed successfully"}
@app.options("/chat")
async def chat_options(request: Request):
    return {}
@app.post("/chat")
async def chat(request: Request):
    global vectorstore
    
    message = await request.json()
    print(f"Received chat message: {message}")
    
    if vectorstore is None:
        return {"response": "Please upload a document first."}
    
    try:
        # Implement chat functionality using ConversationalRetrievalChain
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        qa = ConversationalRetrievalChain.from_llm(
            llm,
            retriever=retriever,
            return_source_documents=True,
            verbose=True
        )
        result = qa({"question": message["message"], "chat_history": []})
        
        sources = [doc.page_content for doc in result["source_documents"]]
        
        print("Chat response generated successfully")
        return {
            "response": result["answer"],
            "sources": sources
        }
    except Exception as e:
        print(f"Error generating chat response: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)