"""
Orion Frontend - Streamlit Web Interface for Cypher RAG

A user-friendly web interface for querying the Neo4j graph database
using natural language queries.
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Add parent directory to path to import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.cypher_rag import CypherRAG
from src.database.neo4j_connection import Neo4jConnection
import pandas as pd
from datetime import datetime


# Page configuration
st.set_page_config(
    page_title="Orion - Graph Query Interface",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .query-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .result-box {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #e0e0e0;
    }
    .cypher-query {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 5px;
        font-family: 'Courier New', monospace;
        border-left: 4px solid #1f77b4;
    }
    .error-box {
        background-color: #fee;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #d32f2f;
        color: #c62828;
    }
    .success-box {
        background-color: #e8f5e9;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #4caf50;
        color: #2e7d32;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def init_rag_service():
    """Initialize Cypher RAG service (cached)."""
    try:
        model = st.session_state.get('model', 'llama3.2')
        rag = CypherRAG(model_name=model)
        if not rag.is_available():
            return None, "Cypher RAG is not available. Please ensure Ollama is running."
        return rag, None
    except Exception as e:
        return None, f"Error initializing RAG service: {e}"


@st.cache_resource
def init_neo4j_connection():
    """Initialize Neo4j connection (cached)."""
    try:
        conn = Neo4jConnection()
        if conn.connect():
            return conn, None
        return None, "Failed to connect to Neo4j. Please check your connection settings."
    except Exception as e:
        return None, f"Error connecting to Neo4j: {e}"


def format_results_as_dataframe(results):
    """Convert query results to pandas DataFrame."""
    if not results:
        return pd.DataFrame()
    
    # Convert list of dicts to DataFrame
    df = pd.DataFrame(results)
    return df


def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown('<div class="main-header">🔍 Orion Graph Query Interface</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Query your Neo4j graph database using natural language</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Model selection
        model_options = ['llama3.2', 'llama3', 'llama2', 'mistral', 'codellama']
        selected_model = st.selectbox(
            "LLM Model",
            model_options,
            index=0,
            help="Select the Ollama model to use for query generation"
        )
        st.session_state['model'] = selected_model
        
        # Max rows
        max_rows = st.slider(
            "Max Results",
            min_value=10,
            max_value=200,
            value=50,
            step=10,
            help="Maximum number of results to display"
        )
        
        st.divider()
        
        # Example queries
        st.header("📝 Example Queries")
        example_queries = [
            "Find all companies",
            "Who works at Apple Inc?",
            "Find all CEOs",
            "Show me companies in the banking sector",
            "What events happened at Apple Inc?",
            "Find all acquisition events",
            "What companies does Apple own?",
            "Find subsidiaries of Banco Santander",
            "Show me directors at companies",
            "Find companies with more than 5 employees"
        ]
        
        for i, example in enumerate(example_queries):
            if st.button(f"💡 {example}", key=f"example_{i}", use_container_width=True):
                st.session_state['query_text'] = example
        
        st.divider()
        
        # Connection status
        st.header("🔌 Connection Status")
        rag, rag_error = init_rag_service()
        conn, conn_error = init_neo4j_connection()
        
        if rag and not rag_error:
            st.success("✅ Cypher RAG: Connected")
        else:
            st.error(f"❌ Cypher RAG: {rag_error or 'Not connected'}")
        
        if conn and not conn_error:
            st.success("✅ Neo4j: Connected")
        else:
            st.error(f"❌ Neo4j: {conn_error or 'Not connected'}")
        
        st.divider()
        
        # Info
        st.info("""
        **How to use:**
        1. Enter your question in natural language
        2. Click "Query" to generate and execute
        3. View results and generated Cypher query
        
        **Tips:**
        - Be specific about what you're looking for
        - Use company names, roles, or event types
        - Check the generated Cypher to learn the syntax
        """)
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Query input
        query_text = st.text_area(
            "💬 Enter your question:",
            value=st.session_state.get('query_text', ''),
            height=100,
            placeholder="e.g., Find all companies or Who works at Apple Inc?",
            key='query_input'
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        show_cypher = st.checkbox("Show Cypher Query", value=True)
        auto_execute = st.checkbox("Auto-execute", value=False, help="Automatically execute query when generated")
    
    # Query button
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        query_button = st.button("🔍 Query", type="primary", use_container_width=True)
    with col2:
        clear_button = st.button("🗑️ Clear", use_container_width=True)
    
    if clear_button:
        st.session_state['query_text'] = ''
        st.session_state['last_query'] = None
        st.session_state['last_results'] = None
        st.session_state['last_cypher'] = None
        st.rerun()
    
    # Initialize services
    rag, rag_error = init_rag_service()
    conn, conn_error = init_neo4j_connection()
    
    if not rag or rag_error:
        st.error(f"**Cypher RAG Error:** {rag_error}")
        st.info("💡 Make sure Ollama is running: `docker-compose up -d ollama`")
        return
    
    if not conn or conn_error:
        st.error(f"**Neo4j Error:** {conn_error}")
        st.info("💡 Make sure Neo4j is running: `docker-compose up -d neo4j`")
        return
    
    # Execute query
    if query_button and query_text:
        with st.spinner("🤖 Generating Cypher query..."):
            try:
                # Generate Cypher query
                cypher_query = rag.generate_cypher(query_text)
                
                if show_cypher:
                    st.markdown("### 📝 Generated Cypher Query")
                    st.markdown(f'<div class="cypher-query">{cypher_query}</div>', unsafe_allow_html=True)
                
                # Execute query
                with st.spinner("⚡ Executing query..."):
                    results, error, final_cypher = rag.query_with_retry(
                        query_text,
                        conn,
                        max_retries=2
                    )
                
                if error:
                    st.markdown("### ❌ Error")
                    st.markdown(f'<div class="error-box"><strong>Error:</strong> {error}</div>', unsafe_allow_html=True)
                    if final_cypher:
                        st.markdown("**Generated Query:**")
                        st.code(final_cypher, language='cypher')
                else:
                    # Store in session state
                    st.session_state['last_query'] = query_text
                    st.session_state['last_results'] = results
                    st.session_state['last_cypher'] = final_cypher
                    
                    # Display results
                    if results:
                        st.markdown("### ✅ Results")
                        st.markdown(f'<div class="success-box">Found <strong>{len(results)}</strong> result(s)</div>', unsafe_allow_html=True)
                        
                        # Convert to DataFrame
                        df = format_results_as_dataframe(results)
                        
                        if not df.empty:
                            # Display as table
                            st.dataframe(df, use_container_width=True, height=400)
                            
                            # Download button
                            csv = df.to_csv(index=False)
                            st.download_button(
                                label="📥 Download Results as CSV",
                                data=csv,
                                file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                    else:
                        st.info("No results found for this query.")
            
            except Exception as e:
                st.error(f"**Error:** {str(e)}")
                st.exception(e)
    
    # Display last results if available
    if st.session_state.get('last_results') and not query_button:
        st.markdown("### 📊 Last Query Results")
        st.info(f"**Query:** {st.session_state.get('last_query')}")
        
        if show_cypher and st.session_state.get('last_cypher'):
            with st.expander("📝 View Generated Cypher Query"):
                st.code(st.session_state['last_cypher'], language='cypher')
        
        df = format_results_as_dataframe(st.session_state['last_results'])
        if not df.empty:
            st.dataframe(df, use_container_width=True, height=400)
    
    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p>Orion Graph Query Interface | Powered by Streamlit & Ollama</p>
        <p>Query your Neo4j graph database using natural language</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

