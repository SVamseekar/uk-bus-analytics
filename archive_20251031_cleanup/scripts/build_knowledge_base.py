"""
Build Policy Q&A Knowledge Base
================================
Creates semantic search index from policy questions and data

Author: UK Bus Analytics Platform
Date: 2025-10-30
"""

import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from dashboard.utils.semantic_search import PolicyQASystem, create_policy_knowledge_base

def main():
    """Build and save the knowledge base"""

    print("🔨 Building Policy Q&A Knowledge Base...")
    print("=" * 60)

    # Paths
    spatial_answers_path = BASE_DIR / "analytics" / "outputs" / "spatial" / "spatial_answers.json"
    output_path = BASE_DIR / "models" / "policy_qa_system"

    # Create output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create knowledge base
    print("\n1️⃣ Creating Q&A pairs from data...")
    qa_pairs = create_policy_knowledge_base(str(spatial_answers_path))
    print(f"   ✅ Created {len(qa_pairs)} Q&A pairs")

    # Build system
    print("\n2️⃣ Building semantic search index...")
    qa_system = PolicyQASystem()
    qa_system.build_knowledge_base(qa_pairs)

    # Save
    print("\n3️⃣ Saving to disk...")
    qa_system.save(str(output_path))

    # Test
    print("\n4️⃣ Testing system...")
    test_queries = [
        "How do I calculate BCR?",
        "What areas have poor bus coverage?",
        "How much does increasing frequency cost?"
    ]

    for query in test_queries:
        results = qa_system.search(query, top_k=1)
        print(f"\n   Q: {query}")
        print(f"   A: {results[0]['answer'][:100]}...")
        print(f"   Confidence: {results[0]['score']:.0%}")

    print("\n" + "=" * 60)
    print("✅ Knowledge base built successfully!")
    print(f"📁 Saved to: {output_path}")
    print("\n🚀 Ready to use in Policy Intelligence Assistant!")

if __name__ == "__main__":
    main()
