#!/usr/bin/env python
"""Shared RAG setup functions"""

import os
from pathlib import Path
from dotenv import load_dotenv

from raganything import RAGAnything, RAGAnythingConfig
from lightrag import LightRAG
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc
import numpy as np
from openai import AsyncOpenAI


load_dotenv()


def get_rag_instance(
    pdk_name: str = "skywater130",
    for_ingestion: bool = False
):
    """
    Get RAG instance for ingestion or querying
    
    Args:
        pdk_name: Name of the PDK
        for_ingestion: True for ingestion (new data), False for querying (existing data)
    
    Returns:
        RAGAnything instance
    """
    api_key = os.getenv("OPENAI_API_KEY")
    working_dir = f"./working_dir/{pdk_name}"
    
    # LLM function
    def llm_func(prompt, system_prompt=None, history_messages=[], **kwargs):
        return openai_complete_if_cache(
                "gpt-4o-mini", 
                prompt,
                system_prompt=system_prompt,
                history_messages=history_messages,
                api_key=api_key, 
                **kwargs
            )
    
    # Vision function
    def vision_func(prompt, system_prompt=None, history_messages=[],
                   image_data=None, messages=None, **kwargs):
        if messages:
            return openai_complete_if_cache(
                "gpt-4o",
                "", 
                system_prompt=None,
                messages=messages,
                api_key=api_key,
                **kwargs
            )
        elif image_data:
            return openai_complete_if_cache(
                "gpt-4o", "", messages=[
                    {"role": "system", "content": system_prompt} if system_prompt else None,
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                    ]}
                ],
                api_key=api_key, **kwargs
            )
        else:
            return llm_func(prompt, system_prompt, history_messages, **kwargs)
    
    
    
    async def openai_embed(texts):
        client = AsyncOpenAI(api_key=api_key)
        
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            return np.array([]) # Return empty numpy array

        response = await client.embeddings.create(
            model="text-embedding-3-large",
            input=texts
        )
        
        # OpenAI model returns an object with many fields and metadata. 
        # LightRAG only wants the data AKA the embeddings.        
        embeddings = [item.embedding for item in response.data]
            
        # Converting to numpy to enable similarity calcs by LightRAG
        return np.array(embeddings)
    
    embedding_func = EmbeddingFunc(
    embedding_dim=3072,
    max_token_size=8192,
    func=openai_embed
    )
    
    # RAG config
    config = RAGAnythingConfig(
        working_dir=working_dir,
        parser="mineru",
        parse_method="auto",
        enable_image_processing=True,
        enable_table_processing=True,
        enable_equation_processing=True
    )
    
    if for_ingestion:
        # For ingestion: create fresh RAG instance
        rag = RAGAnything(
            config=config,
            llm_model_func=llm_func,
            vision_model_func=vision_func,
            embedding_func=embedding_func,
        )
    else:
        # For querying: load existing LightRAG instance
        if not Path(working_dir).exists():
            raise FileNotFoundError(
                f"No data found for {pdk_name}. Run ingestion first."
            )
        
        lightrag_instance = LightRAG(
            working_dir=working_dir,
            llm_model_func=llm_func,
            embedding_func=embedding_func
        )
        
        rag = RAGAnything(
            config=config,
            lightrag=lightrag_instance,
            vision_model_func=vision_func,
        )
    
    return rag