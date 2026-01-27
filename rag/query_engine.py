#!/usr/bin/env python
"""Query engine for PDK documentation"""

import asyncio
import logging
from rag_helper import get_rag_instance

logging.getLogger("lightrag").setLevel(logging.WARNING)
logging.getLogger("nano-vectordb").setLevel(logging.WARNING)

class PDKQueryEngine:
    """Simple query engine for PDK documentation"""
    
    def __init__(self, pdk_name: str = "skywater130"):
        self.pdk_name = pdk_name
        self._rag = None
    
    def _get_rag(self):
        """Lazy load RAG instance"""
        if self._rag is None:
            print(f"Loading RAG system for {self.pdk_name}...")
            self._rag = get_rag_instance(pdk_name=self.pdk_name, for_ingestion=False)
            print(f"RAG system loaded")
        return self._rag
    
    async def query(self, question: str, mode: str = "hybrid"):
        """        
        Args:
            question: Question to ask
            mode: Query mode - 'naive', 'local', 'global', or 'hybrid'
        """
        rag = self._get_rag()
        result = await rag.aquery(question, mode=mode, top_k=19, enable_rerank=False)
        return result


# Quick test
if __name__ == "__main__":
    async def test():
        print("Testing PDK Query Engine")
        
        engine = PDKQueryEngine("skywater130")
        
        test_questions = [
            "What is this PDK? Be Brief",
            "What are the main topics covered? Be Brief",
            "How many different transistor types are there? Describe each one briefly."
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"Query {i}: {question}")
            
            try:
                result = await engine.query(question)
                print(f"Answer: {result}...")
                print()
            except Exception as e:
                print(f"Error: {e}")
                print()
        
    
    asyncio.run(test())