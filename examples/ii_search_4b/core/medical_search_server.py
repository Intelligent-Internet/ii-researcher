"""Medical Search Server

FastAPI-based medical literature search server using BM25 retrieval.
Provides endpoints for searching PubMed articles and retrieving content.
"""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List, Optional, Any

import bm25s
import uvicorn
from bm25s.hf import BM25HF
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from tqdm import tqdm


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import configuration with proper error handling
try:
    from ..configs import LOCAL_STORAGE, RAG_URL
except ImportError:
    try:
        sys.path.append(str(Path(__file__).parent.parent))
        from configs import LOCAL_STORAGE, RAG_URL
    except ImportError as e:
        logger.error(f"Failed to import configuration: {e}")
        raise RuntimeError(
            "Configuration import failed. Ensure configs.py exists."
        ) from e


class MedicalSearchConfig:
    """Configuration class for the Medical Search Server."""

    def __init__(self):
        self.local_storage = LOCAL_STORAGE
        self.rag_url = RAG_URL
        self.model_name = "meoconxinhxan/MedicalBm25-PubMed"
        self.timeout = 6000
        self.max_results = 50
        self.preview_length = 256

    def validate(self) -> None:
        """Validate configuration parameters."""
        if not self.local_storage:
            raise ValueError("LOCAL_STORAGE must be specified")
        if not self.rag_url:
            raise ValueError("RAG_URL must be specified")

        # Create storage directory if it doesn't exist
        Path(self.local_storage).mkdir(parents=True, exist_ok=True)
        logger.info(f"Using storage directory: {self.local_storage}")


class MedicalSearchService:
    """Service class for medical literature search operations."""

    def __init__(self, config: MedicalSearchConfig):
        self.config = config
        self.retriever = None
        self.index_to_corpus = {}
        self._is_initialized = False

    async def initialize(self) -> None:
        """Initialize the BM25 retriever and build URL index."""
        if self._is_initialized:
            return

        try:
            logger.info(f"Loading BM25 model: {self.config.model_name}")
            self.retriever = BM25HF.load_from_hub(
                self.config.model_name,
                local_dir=self.config.local_storage,
                load_corpus=True,
            )
            logger.info(f"Loaded {len(self.retriever.corpus)} documents")

            # Build URL to corpus index mapping
            logger.info("Building URL index...")
            for index in tqdm(range(len(self.retriever.corpus)), desc="Indexing URLs"):
                document = self.retriever.corpus[index]
                if "id" in document:
                    idx = document["id"]
                    url = f"https://pubmed.gov/article/{idx}"
                    self.index_to_corpus[url] = index

            logger.info(f"Built index with {len(self.index_to_corpus)} URL mappings")
            self._is_initialized = True

        except Exception as e:
            logger.error(f"Failed to initialize medical search service: {e}")
            raise RuntimeError(f"Service initialization failed: {e}") from e

    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for medical documents.

        Args:
            query: Search query string
            top_k: Number of results to return

        Returns:
            List of search results with metadata

        Raises:
            RuntimeError: If service is not initialized
            ValueError: If query is invalid
        """
        if not self._is_initialized:
            raise RuntimeError("Service not initialized. Call initialize() first.")

        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        if top_k <= 0 or top_k > self.config.max_results:
            raise ValueError(f"top_k must be between 1 and {self.config.max_results}")

        try:
            logger.info(f"Searching for: '{query[:100]}...' (top_k={top_k})")

            results = self.retriever.retrieve(bm25s.tokenize(query), k=top_k)
            documents = results.documents.tolist()[0][:top_k]
            scores = results.scores.tolist()[0][:top_k]

            search_results = []
            for document, score in zip(documents, scores):
                if "id" not in document:
                    logger.warning("Document missing 'id' field, skipping")
                    continue

                idx = document["id"]
                url = f"https://pubmed.gov/article/{idx}"

                result = {
                    "url": url,
                    "paper_id": idx,
                    "title": document.get("title", "No title available"),
                    "preview": document.get("content", "")[
                        : self.config.preview_length
                    ],
                    "score": float(score),
                    "has_full_content": url in self.index_to_corpus,
                }
                search_results.append(result)

            logger.info(f"Found {len(search_results)} results")
            return search_results

        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            raise RuntimeError(f"Search operation failed: {e}") from e

    async def get_document_content(self, url: str) -> Dict[str, Any]:
        """Retrieve full document content by URL.

        Args:
            url: Document URL

        Returns:
            Dictionary containing document content and metadata

        Raises:
            RuntimeError: If service is not initialized
            ValueError: If URL is not found
        """
        if not self._is_initialized:
            raise RuntimeError("Service not initialized. Call initialize() first.")

        if url not in self.index_to_corpus:
            raise ValueError(f"Document not found: {url}")

        try:
            index = self.index_to_corpus[url]
            document = self.retriever.corpus[index]

            return {
                "url": url,
                "paper_id": document.get("id", "unknown"),
                "title": document.get("title", "No title available"),
                "content": document.get("content", ""),
                "metadata": {
                    "corpus_index": index,
                    "content_length": len(document.get("content", "")),
                },
            }

        except Exception as e:
            logger.error(f"Failed to retrieve document {url}: {e}")
            raise RuntimeError(f"Document retrieval failed: {e}") from e


# Global service instance
config = MedicalSearchConfig()
service = MedicalSearchService(config)


# Pydantic models for API requests and responses
class SearchQuery(BaseModel):
    """Request model for search endpoint."""

    query: str = Field(
        ..., min_length=1, max_length=1000, description="Search query string"
    )
    top_k: int = Field(
        default=5, ge=1, le=50, description="Number of results to return"
    )

    @validator("query")
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        return v.strip()


class SearchResult(BaseModel):
    """Model for individual search result."""

    url: str = Field(..., description="Document URL")
    paper_id: str = Field(..., description="PubMed paper ID")
    title: str = Field(..., description="Document title")
    preview: str = Field(..., description="Content preview")
    score: float = Field(..., description="Relevance score")
    has_full_content: bool = Field(..., description="Whether full content is available")


class SearchResponse(BaseModel):
    """Response model for search endpoint."""

    results: List[SearchResult] = Field(..., description="List of search results")
    query: str = Field(..., description="Original query")
    total_results: int = Field(..., description="Number of results returned")
    max_score: Optional[float] = Field(None, description="Highest relevance score")


class VisitRequest(BaseModel):
    """Request model for visit endpoint."""

    url: str = Field(..., description="Document URL to visit")

    @validator("url")
    def validate_url(cls, v):
        if not v.startswith("https://pubmed.gov/article/"):
            raise ValueError("URL must be a valid PubMed article URL")
        return v


class DocumentMetadata(BaseModel):
    """Model for document metadata."""

    corpus_index: int = Field(..., description="Index in corpus")
    content_length: int = Field(..., description="Content length in characters")


class VisitResponse(BaseModel):
    """Response model for visit endpoint."""

    url: str = Field(..., description="Document URL")
    paper_id: str = Field(..., description="PubMed paper ID")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Full document content")
    metadata: DocumentMetadata = Field(..., description="Document metadata")
    status_code: int = Field(default=200, description="HTTP status code")


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(..., description="Service status")
    service_name: str = Field(..., description="Service name")
    version: str = Field(..., description="API version")
    initialized: bool = Field(..., description="Whether service is initialized")
    corpus_size: Optional[int] = Field(
        None, description="Number of documents in corpus"
    )


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    status_code: int = Field(..., description="HTTP status code")


# FastAPI app with lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    logger.info("Starting Medical Search API...")
    try:
        config.validate()
        await service.initialize()
        logger.info("Medical Search API started successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down Medical Search API...")


app = FastAPI(
    title="Medical Search API",
    description="FastAPI-based medical literature search server using BM25 retrieval for PubMed articles",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post(
    "/search",
    response_model=SearchResponse,
    summary="Search Medical Literature",
    description="Search for medical documents using BM25 retrieval",
    responses={
        200: {"description": "Search completed successfully"},
        400: {"description": "Invalid search query", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
async def search_documents(search_query: SearchQuery) -> SearchResponse:
    """Search for medical documents using BM25 retrieval.

    Args:
        search_query: Search parameters including query string and result count

    Returns:
        SearchResponse containing search results and metadata

    Raises:
        HTTPException: If search fails or query is invalid
    """
    try:
        results = await service.search(search_query.query, search_query.top_k)

        search_results = [SearchResult(**result) for result in results]

        max_score = max((r.score for r in search_results), default=None)

        return SearchResponse(
            results=search_results,
            query=search_query.query,
            total_results=len(search_results),
            max_score=max_score,
        )

    except ValueError as e:
        logger.warning(f"Invalid search query: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid query: {str(e)}"
        )
    except RuntimeError as e:
        logger.error(f"Search service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search service unavailable",
        )
    except Exception as e:
        logger.error(f"Unexpected error during search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )


@app.post(
    "/visit",
    response_model=VisitResponse,
    summary="Retrieve Document Content",
    description="Retrieve full content of a medical document by URL",
    responses={
        200: {"description": "Document retrieved successfully"},
        400: {"description": "Invalid URL", "model": ErrorResponse},
        404: {"description": "Document not found", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
async def visit_document(request: VisitRequest) -> VisitResponse:
    """Retrieve full content of a medical document.

    Args:
        request: Visit request containing the document URL

    Returns:
        VisitResponse containing document content and metadata

    Raises:
        HTTPException: If document is not found or retrieval fails
    """
    try:
        document_data = await service.get_document_content(request.url)

        return VisitResponse(
            url=document_data["url"],
            paper_id=document_data["paper_id"],
            title=document_data["title"],
            content=document_data["content"],
            metadata=DocumentMetadata(**document_data["metadata"]),
            status_code=200,
        )

    except ValueError as e:
        logger.warning(f"Document not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {request.url}",
        )
    except RuntimeError as e:
        logger.error(f"Document retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document retrieval service unavailable",
        )
    except Exception as e:
        logger.error(f"Unexpected error during document visit: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Get service health status and information",
)
async def health_check() -> HealthResponse:
    """Check service health and return status information.

    Returns:
        HealthResponse containing service status and metadata
    """
    corpus_size = None
    if service._is_initialized and service.retriever:
        corpus_size = len(service.retriever.corpus)

    return HealthResponse(
        status="healthy" if service._is_initialized else "initializing",
        service_name="Medical Search API",
        version="1.0.0",
        initialized=service._is_initialized,
        corpus_size=corpus_size,
    )


def main():
    """Main entry point for the medical search server."""
    try:
        port = int(RAG_URL.split(":")[-1])
        logger.info(f"Starting server on port {port}")

        uvicorn.run(
            "core.medical_search_server:app",
            host="0.0.0.0",
            port=port,
            workers=1,
            log_level="info",
            access_log=True,
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise


if __name__ == "__main__":
    main()
