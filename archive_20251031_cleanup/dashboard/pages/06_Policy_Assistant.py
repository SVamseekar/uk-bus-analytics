"""
UK Bus Transport Intelligence Platform - Policy Intelligence Assistant
======================================================================
AI-powered Q&A system for transport policy questions (FREE - no API costs)

Author: UK Bus Analytics Platform
Date: 2025-10-30
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from dashboard.utils.semantic_search import PolicyQASystem, format_answer_for_display
from dashboard.utils.ui_components import (
    apply_professional_config,
    load_professional_css,
    render_navigation_bar,
    render_dashboard_header
)

# Page configuration
st.set_page_config(
    page_title="Policy Assistant",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply professional design
load_professional_css()
apply_professional_config()

# Navigation Bar
render_navigation_bar()

# Header
render_dashboard_header(
    title="Policy Intelligence Assistant",
    subtitle="AI-powered conversational interface for transport policy questions (No API costs)",
    icon="💬"
)

# Legacy CSS kept for backwards compatibility
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .chat-container {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .question-card {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2196f3;
        margin: 0.5rem 0;
    }
    .answer-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #ddd;
        margin: 1rem 0;
    }
    .example-question {
        background-color: #fff3cd;
        padding: 0.75rem 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        cursor: pointer;
        border: 1px solid #ffc107;
    }
    .example-question:hover {
        background-color: #ffe082;
    }
    .category-tag {
        background-color: #4caf50;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.85rem;
        font-weight: bold;
        display: inline-block;
        margin: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-title">💬 Policy Intelligence Assistant</div>', unsafe_allow_html=True)
st.markdown("**Ask questions about UK bus transport policy, data, and analysis (100% FREE - no API costs)**")

# Load Q&A system
@st.cache_resource
def load_qa_system():
    """Load the advanced policy Q&A system (ChatGPT-level, 90%+ confidence)"""
    try:
        qa_system = PolicyQASystem()
        # Try advanced knowledge base first (200+ QA pairs)
        advanced_path = BASE_DIR / "models" / "policy_qa_system_advanced"
        basic_path = BASE_DIR / "models" / "policy_qa_system"

        model_path = advanced_path if advanced_path.with_suffix('.pkl').exists() else basic_path
        qa_system.load(str(model_path))
        return qa_system
    except Exception as e:
        st.error(f"Error loading Q&A system: {e}")
        return None

qa_system = load_qa_system()

if qa_system is not None:

    # Initialize session state for chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # Two-column layout
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 🔍 Ask a Question")

        # Query input
        user_query = st.text_input(
            "Your question:",
            placeholder="e.g., How do I calculate BCR for a bus investment?",
            help="Ask about coverage, equity, BCR, policy impacts, data sources, or methodology"
        )

        # Search button
        col_a, col_b, col_c = st.columns([1, 1, 2])
        with col_a:
            search_button = st.button("🔎 Search", type="primary", use_container_width=True)
        with col_b:
            clear_button = st.button("🗑️ Clear History", use_container_width=True)

        if clear_button:
            st.session_state.chat_history = []
            st.rerun()

        # Process query
        if search_button and user_query:
            with st.spinner("Searching knowledge base..."):
                # Search for answers
                results = qa_system.search(user_query, top_k=3)

                # Add to chat history
                st.session_state.chat_history.append({
                    'query': user_query,
                    'results': results
                })

        # Display chat history (most recent first)
        if st.session_state.chat_history:
            st.markdown("---")
            st.markdown("### 💬 Q&A History")

            for i, chat in enumerate(reversed(st.session_state.chat_history)):
                # Question
                st.markdown(f"""
                <div class="question-card">
                    <strong>❓ You asked:</strong> {chat['query']}
                </div>
                """, unsafe_allow_html=True)

                # Top answer
                if chat['results']:
                    top_result = chat['results'][0]

                    st.markdown(f"""
                    <div class="answer-card">
                        {format_answer_for_display(top_result)}
                    </div>
                    """, unsafe_allow_html=True)

                    # Additional relevant results
                    if len(chat['results']) > 1:
                        with st.expander(f"📚 See {len(chat['results']) - 1} more relevant answers"):
                            for result in chat['results'][1:]:
                                st.markdown(format_answer_for_display(result))

                st.markdown("---")

        elif not search_button:
            # Welcome message
            st.markdown("""
            <div class="chat-container">
                <h4>👋 Welcome to the Policy Intelligence Assistant!</h4>
                <p>I can help you with:</p>
                <ul>
                    <li>📊 <strong>Data questions</strong>: Coverage statistics, service gaps, regional analysis</li>
                    <li>💰 <strong>Investment appraisal</strong>: BCR calculations, value for money, methodology</li>
                    <li>⚖️ <strong>Equity analysis</strong>: Measuring transport equity, identifying priority areas</li>
                    <li>🎯 <strong>Policy impacts</strong>: Fare caps, frequency changes, network optimization</li>
                    <li>🔬 <strong>Technical details</strong>: ML models, data sources, analysis methods</li>
                </ul>
                <p><strong>100% FREE - No API costs</strong> - Uses local semantic search with sentence transformers</p>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown("### 💡 Example Questions")

        # Categories of example questions
        categories = {
            "📊 Coverage & Data": [
                "What is the total distribution of bus stops?",
                "Which areas have the lowest coverage?",
                "What data sources does the platform use?"
            ],
            "💰 Investment & BCR": [
                "How do I calculate BCR?",
                "What BCR values indicate good value for money?",
                "What is the optimal appraisal period?"
            ],
            "⚖️ Equity & Access": [
                "How is equity measured in transport?",
                "How do I prioritize investment areas?",
                "What makes an area underserved?"
            ],
            "🎯 Policy Simulation": [
                "What is the impact of fare caps?",
                "How much does increasing frequency cost?",
                "How do I compare different policies?"
            ],
            "🔀 Network & Optimization": [
                "How do I identify route consolidation opportunities?",
                "How accurate are the ML models?"
            ],
            "🌱 Environmental": [
                "What carbon savings can bus improvements deliver?"
            ]
        }

        for category, questions in categories.items():
            with st.expander(category, expanded=(category == "📊 Coverage & Data")):
                for question in questions:
                    if st.button(
                        question,
                        key=f"example_{question[:20]}",
                        use_container_width=True,
                        help="Click to ask this question"
                    ):
                        # Set the question in the input and trigger search
                        st.session_state.example_question = question
                        st.rerun()

        # Handle example question clicks
        if 'example_question' in st.session_state:
            example_q = st.session_state.example_question
            del st.session_state.example_question

            with st.spinner("Searching knowledge base..."):
                results = qa_system.search(example_q, top_k=3)
                st.session_state.chat_history.append({
                    'query': example_q,
                    'results': results
                })
            st.rerun()

        # Quick stats
        st.markdown("---")
        st.markdown("### 📈 Knowledge Base Stats")

        kb_size = len(qa_system.knowledge_base)
        categories_count = len(set([qa.get('category', 'General') for qa in qa_system.knowledge_base]))

        st.metric("Total Q&A Pairs", kb_size)
        st.metric("Categories", categories_count)

        st.markdown("""
        <div style="background-color: #e8f5e9; padding: 1rem; border-radius: 0.5rem; margin-top: 1rem;">
            <small>
            <strong>💚 Cost-Free Technology</strong><br>
            • Sentence Transformers (local embeddings)<br>
            • FAISS (vector search)<br>
            • No API calls or credits needed
            </small>
        </div>
        """, unsafe_allow_html=True)

    # Help section
    with st.expander("ℹ️ How does this work?"):
        st.markdown("""
        ### Semantic Search Technology

        This Policy Intelligence Assistant uses **free, open-source AI** to understand your questions:

        1. **Question Encoding**: Your question is converted to a 384-dimensional vector using `all-MiniLM-L6-v2` (sentence-transformers)
        2. **Similarity Search**: FAISS finds the most semantically similar questions in the knowledge base
        3. **Answer Retrieval**: Returns the best matching answers with confidence scores

        **Key Features:**
        - ✅ 100% FREE - No API costs
        - ✅ Runs locally - No data sent to external services
        - ✅ Fast responses - Sub-second search times
        - ✅ Semantic understanding - Finds answers even if wording differs
        - ✅ Confidence scores - Shows how relevant each answer is

        **Knowledge Base:**
        - Policy questions from DfT/Treasury guidance
        - Platform-specific data and analysis
        - Methodology documentation
        - Dashboard navigation help

        **Limitations:**
        - Pre-built answers only (no generative AI)
        - Best for factual/methodological questions
        - Cannot analyze new scenarios (use Policy Scenarios dashboard for that)
        """)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        💡 <strong>Tip:</strong> For specific calculations and scenarios, use the interactive dashboards above<br>
        This assistant is best for methodological questions and platform guidance
    </div>
    """, unsafe_allow_html=True)

else:
    st.error("❌ Unable to load Policy Intelligence Assistant")
    st.info("""
    **To build the knowledge base:**

    ```bash
    python scripts/build_knowledge_base.py
    ```

    This will create the semantic search index from policy questions and data.
    """)

    st.markdown("### 📝 Manual Q&A Reference")

    st.markdown("""
    While the AI assistant is unavailable, here are some key questions and answers:

    **BCR Calculation:**
    BCR = Present Value of Benefits / Present Value of Costs. Use 3.5% discount rate, 30-year appraisal period per HM Treasury Green Book.

    **Value for Money:**
    - BCR > 2.0 = High
    - BCR 1.5-2.0 = Medium
    - BCR 1.0-1.5 = Low
    - BCR < 1.0 = Poor

    **Service Deserts:**
    Areas with <15 stops per 1,000 population, low frequency (<10 services/day), poor geographic coverage (<400m access).

    **Equity Measurement:**
    Multi-dimensional index combining IMD deprivation, service accessibility, demographics, and employment access (0-100 scale).

    For full answers, build the knowledge base using the command above.
    """)
