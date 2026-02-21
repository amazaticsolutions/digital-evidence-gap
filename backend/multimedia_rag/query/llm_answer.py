"""
LLM answer and scoring module using Ollama.

This module provides functionality to use a local LLM (llama3 or mistral)
via Ollama to score search results for relevance and provide explanations.
The LLM analyzes frame captions against the user's query and assigns
confidence scores.

IMPORTANT: This module uses the text-only LLM (llama3/mistral), NOT LLaVA.
LLaVA is used only for generating captions from images.

Functions:
    score_and_answer: Score search results and provide relevance explanations
"""

import json
import re
from typing import List, Dict, Any, Optional

import ollama

from multimedia_rag import config


# Prompt template for scoring results
SCORING_PROMPT_TEMPLATE = """You are a forensic video analyst assistant. Your task is to evaluate how relevant each frame description is to the user's query.

USER QUERY: {query}

Below are descriptions of video frames from surveillance footage. For each frame, analyze how well it matches the query and provide:
1. A relevance score from 0 to 100 (100 = perfect match, 0 = completely irrelevant)
2. Whether it's relevant (true if score > 40, false otherwise)
3. A brief explanation of why it is or isn't relevant

FRAME DESCRIPTIONS:
{frame_descriptions}

Respond ONLY with a valid JSON array. Each element should have this exact structure:
[
  {{
    "frame_id": "frame_id_here",
    "score": 85,
    "relevant": true,
    "explanation": "Brief explanation here"
  }}
]

Important:
- Be precise in your scoring. A partial match should get a moderate score (40-70).
- Only give high scores (80+) for very clear matches to the query.
- Consider synonyms and related concepts (e.g., "backpack" could match "bag", "rucksack").
- Focus on the specific elements mentioned in the query.

Respond with the JSON array only, no additional text:"""


def _parse_llm_response(response_text: str) -> List[Dict[str, Any]]:
    """
    Parse the LLM response to extract the JSON array.
    
    Handles cases where the LLM might include extra text around the JSON.
    
    Args:
        response_text: Raw text response from the LLM.
    
    Returns:
        List[Dict]: Parsed list of score dictionaries.
    
    Raises:
        ValueError: If JSON cannot be parsed from the response.
    """
    # Clean the response text
    text = response_text.strip()
    
    # Try to find JSON array in the response
    # Look for content between [ and ]
    json_match = re.search(r'\[[\s\S]*\]', text)
    
    if json_match:
        json_str = json_match.group(0)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON from LLM response: {e}")
    
    # If no array found, try parsing the whole response
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
        elif isinstance(result, dict):
            return [result]
    except json.JSONDecodeError:
        pass
    
    raise ValueError(
        f"Could not extract valid JSON from LLM response. "
        f"Response preview: {text[:200]}..."
    )


def score_and_answer(
    query: str,
    results: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Score search results for relevance using the LLM and provide explanations.
    
    This function sends the user query and all result captions to the LLM
    (llama3 or mistral via Ollama) for analysis. The LLM scores each result
    from 0-100 for relevance and provides an explanation.
    
    Args:
        query: The user's natural language query (e.g., "Show me every 
            instance of the red backpack being dropped").
        results: List of search results from vector_search, each containing:
            - _id (str): Frame identifier
            - caption (str): Frame description
            - cam_id (str): Camera identifier
            - timestamp (int): Second in video
            - And other fields...
    
    Returns:
        List[Dict]: The input results list enriched with additional fields:
            - score (float): Relevance score 0-100 (overwrites vector score)
            - relevant (bool): True if score > 40
            - explanation (str): Why the frame is or isn't relevant
        Results are sorted by score descending (most relevant first).
    
    Raises:
        ConnectionError: If unable to connect to Ollama server.
        RuntimeError: If the LLM fails to generate a valid response.
        ValueError: If results list is empty or query is empty.
    
    Example:
        >>> results = vector_search(query_embedding)
        >>> scored = score_and_answer("red backpack dropped", results)
        >>> for r in scored[:3]:
        ...     print(f"{r['_id']}: {r['score']}/100 - {r['explanation']}")
        cam1_t142: 95/100 - Frame shows person dropping a red backpack
        cam1_t143: 88/100 - Red backpack visible on ground near person
        cam2_t051: 42/100 - Person with backpack but color not clearly red
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    
    if not results:
        raise ValueError("Results list cannot be empty")
    
    # Build frame descriptions for the prompt
    frame_descriptions = []
    for i, result in enumerate(results):
        frame_id = result.get('_id', f'frame_{i}')
        caption = result.get('caption', 'No description available')
        cam_id = result.get('cam_id', 'unknown')
        timestamp = result.get('timestamp', 0)
        
        frame_descriptions.append(
            f"Frame {i+1}:\n"
            f"  ID: {frame_id}\n"
            f"  Camera: {cam_id}\n"
            f"  Timestamp: {timestamp}s\n"
            f"  Description: {caption}"
        )
    
    frame_descriptions_text = "\n\n".join(frame_descriptions)
    
    # Build the full prompt
    prompt = SCORING_PROMPT_TEMPLATE.format(
        query=query,
        frame_descriptions=frame_descriptions_text
    )
    
    try:
        # Create Ollama client
        client = ollama.Client(host=config.OLLAMA_BASE_URL)
        
        # Send prompt to LLM
        print(f"Sending {len(results)} frames to LLM for scoring...")
        response = client.generate(
            model=config.LLM_MODEL,
            prompt=prompt,
            options={
                'temperature': 0.1,  # Low temperature for consistent scoring
                'num_predict': 2000,  # Allow enough tokens for all scores
            }
        )
        
        response_text = response.get('response', '')
        
        if not response_text:
            raise RuntimeError("LLM returned an empty response")
        
        # Parse the JSON response
        scores = _parse_llm_response(response_text)
        
        # Create a lookup dict for scores by frame_id
        scores_lookup = {s['frame_id']: s for s in scores}
        
        # Merge scores into results
        enriched_results = []
        for result in results:
            frame_id = result.get('_id')
            enriched = result.copy()
            
            if frame_id in scores_lookup:
                score_data = scores_lookup[frame_id]
                enriched['score'] = score_data.get('score', 0)
                enriched['relevant'] = score_data.get('relevant', False)
                enriched['explanation'] = score_data.get('explanation', 'No explanation provided')
            else:
                # Frame wasn't in LLM response, assign default low score
                enriched['score'] = 0
                enriched['relevant'] = False
                enriched['explanation'] = 'Frame not scored by LLM'
            
            enriched_results.append(enriched)
        
        # Sort by score descending
        enriched_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        print(f"Scoring complete. {sum(1 for r in enriched_results if r.get('relevant'))} relevant results found.")
        
        return enriched_results
        
    except ollama.ResponseError as e:
        raise RuntimeError(f"LLM model error: {str(e)}")
    except Exception as e:
        # Check if it's a connection error
        if "connection" in str(e).lower() or "refused" in str(e).lower():
            raise ConnectionError(
                f"Could not connect to Ollama server at {config.OLLAMA_BASE_URL}. "
                "Ensure Ollama is running with: ollama serve"
            )
        raise RuntimeError(f"Scoring failed: {str(e)}")


def check_llm_available() -> bool:
    """
    Check if the LLM model is available on the Ollama server.
    
    Returns:
        bool: True if the configured LLM is available, False otherwise.
    """
    try:
        client = ollama.Client(host=config.OLLAMA_BASE_URL)
        models = client.list()
        
        # Check if configured LLM model exists
        model_names = [m.get('name', '').split(':')[0] for m in models.get('models', [])]
        return config.LLM_MODEL in model_names
        
    except Exception:
        return False


def generate_summary(query: str, relevant_results: List[Dict[str, Any]]) -> str:
    """
    Generate a natural language summary of the findings.
    
    Args:
        query: The user's original query.
        relevant_results: List of relevant results with scores and explanations.
    
    Returns:
        str: A natural language summary of what was found.
    """
    if not relevant_results:
        return f"No relevant frames found for query: '{query}'"
    
    summary_prompt = f"""Based on these surveillance video analysis results for the query "{query}", 
provide a brief 2-3 sentence summary of what was found:

Results:
{json.dumps([{
    'frame_id': r.get('_id'),
    'cam_id': r.get('cam_id'),
    'timestamp': r.get('timestamp'),
    'score': r.get('score'),
    'explanation': r.get('explanation')
} for r in relevant_results[:5]], indent=2)}

Summary:"""

    try:
        client = ollama.Client(host=config.OLLAMA_BASE_URL)
        response = client.generate(
            model=config.LLM_MODEL,
            prompt=summary_prompt,
            options={'temperature': 0.3, 'num_predict': 200}
        )
        return response.get('response', '').strip()
    except Exception as e:
        # Fallback summary
        return (
            f"Found {len(relevant_results)} relevant frames for '{query}'. "
            f"Top match: {relevant_results[0].get('_id')} with score {relevant_results[0].get('score')}/100."
        )
