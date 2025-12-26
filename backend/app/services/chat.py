import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.services.ai.cypher_rag import CypherRAG
from app.services.vector_rag import VectorRAG
from app.services.database.neo4j_connection import Neo4jConnection
from app.services.database.oracle_connection import OracleConnection

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = "llama3.2"

class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]  # Filings
    graph_path: List[Dict[str, Any]] # Graph nodes/edges
    thought_process: Dict[str, Any] # Debug info

class ChatOrchestrator:
    """
    Orchestrates the Hybrid RAG pipeline:
    1. User Question
    2. Backend -> LLM
    3. LLM -> Cypher
    4. Neo4j -> Facts
    5. VectorDB -> Text
    6. Merge Contexts
    7. LLM -> Final Answer
    8. UI Response
    """
    
    def __init__(self, model_name: str = "llama3.2"):
        self.model_name = model_name
        self.cypher_rag = CypherRAG(model_name=model_name)
        
        # Initialize DB connections
        self.neo4j_conn = Neo4jConnection()
        self.oracle_conn = OracleConnection()
        self.vector_rag = VectorRAG(self.oracle_conn)
        
        # Synthesis LLM
        self.llm = ChatOllama(
            model=model_name,
            temperature=0.3,
            base_url=self.cypher_rag.base_url
        )

    async def process_message(self, request: ChatRequest) -> ChatResponse:
        """Execute the 8-step flow."""
        query = request.message
        thought_process = {"steps": []}
        
        # Step 1: User types question (handled by API)
        logger.info(f"Processing query: {query}")
        
        # Step 2 & 3: LLM generates Cypher (CypherRAG handles this)
        thought_process["steps"].append("Generating Cypher query...")
        self.neo4j_conn.connect()
        
        try:
            # Step 4: Neo4j returns structured facts
            structured_facts, error, cypher_query = self.cypher_rag.query_with_retry(
                query, self.neo4j_conn
            )
            
            thought_process["cypher_query"] = cypher_query
            thought_process["steps"].append("Executed Graph Query")
            
            if error:
                logger.warning(f"Graph query error: {error}")
                structured_facts = []
                
        except Exception as e:
            logger.error(f"Graph pipeline failed: {e}")
            structured_facts = []
            cypher_query = None

        # Step 5: Vector DB returns relevant filing text
        thought_process["steps"].append("Searching Vector DB...")
        vector_docs = self.vector_rag.search(query)
        
        # Step 6: Backend merges both contexts
        context_str = self._build_context(structured_facts, vector_docs)
        thought_process["context_size"] = len(context_str)
        
        # Step 7: LLM generates final answer
        thought_process["steps"].append("Generating Final Answer")
        final_answer = self._generate_answer(query, context_str)
        
        # Step 8: Return structured response
        return ChatResponse(
            answer=final_answer,
            sources=vector_docs,
            graph_path=structured_facts or [],
            thought_process=thought_process
        )

    def _build_context(self, facts: Optional[List[Dict]], docs: List[Dict]) -> str:
        """Merge Graph Facts and Vector Docs into a single context string."""
        context = "CONTEXT FROM KNOWLEDGE GRAPH:\n"
        if facts:
            # Convert list of dicts to string representation
             for i, fact in enumerate(facts[:10], 1): # Limit to top 10 facts
                 context += f"{i}. {fact}\n"
        else:
            context += "No structured facts found.\n"
            
        context += "\nCONTEXT FROM FILINGS (TEXT):\n"
        context += self.vector_rag.format_results(docs)
        
        return context

    def _generate_answer(self, query: str, context: str) -> str:
        """Prompt the LLM to answer based on the merged context."""
        prompt = ChatPromptTemplate.from_template("""
        You are an intelligent financial analyst assistant. 
        Answer the user's question using the provided context.
        
        Context:
        {context}
        
        Question: 
        {question}
        
        Instructions:
        - Cite your sources from the context (e.g., "[Filing 10-K]").
        - If the context mentions relationships (e.g., A owns B), highlight them.
        - If the answer is not in the context, admit it.
        - Be concise and professional.
        """)
        
        chain = prompt | self.llm | StrOutputParser()
        return chain.invoke({"context": context, "question": query})

# Singleton instance
_orchestrator = None

def get_orchestrator():
    global _orchestrator
    if not _orchestrator:
        _orchestrator = ChatOrchestrator()
    return _orchestrator
