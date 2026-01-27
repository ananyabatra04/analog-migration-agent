#!/usr/bin/env python
"""Pipeline to ingest pdf documentation"""

import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from rag_helper import get_rag_instance

load_dotenv()


async def ingest_skywater_pdk(
    pdf_path: str = None,
    working_dir: str = "./working_dir/skywater130",
    output_dir: str = "./output/skywater130"
):
    """Ingest Skywater 130nm PDK documentation"""
    
    try:
        if pdf_path is None:
            pdf_path = Path(__file__).parent / "knowledge-base" / "skywater-pdk-readthedocs-io-en-main.pdf"
        else:
            pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        print(f"📄 Processing: {pdf_path.name}")
        print(f"📂 Working directory: {working_dir}")
        
        # Get RAG instance for ingestion
        print("Initializing RAGAnything")
        rag = get_rag_instance(pdk_name="skywater130", for_ingestion=True)
        
        # Process document
        print("Processing document")
        await rag.process_document_complete(
            file_path=str(pdf_path),
            output_dir=output_dir,
            parse_method="auto",
            start_page=0,
            end_page=30
        )
        
        print("INGESTION COMPLETE")
        print(f"   Index stored in: {working_dir}")
        return True
        
    except Exception as e:
        print(f"INGESTION FAILED WITH REASON: {e}")
        import traceback
        traceback.print_exc()
        return False    


def main():
    print("=" * 50)
    print("Skywater 130nm PDK Ingestion")
    print("=" * 50)
    asyncio.run(ingest_skywater_pdk())


if __name__ == "__main__":
    main()