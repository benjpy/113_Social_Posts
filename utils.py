import os
import requests
import time
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def fetch_text_from_url(url, use_reader=False):
    """
    Fetches and extracts the main text content from a given URL.
    Optionally uses r.jina.ai (Reader Mode) to bypass consent walls.
    Falls back to standard BeautifulSoup fetch if Reader Mode fails.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # 1. Try Reader Mode if enabled
    if use_reader:
        try:
            target_url = f"https://r.jina.ai/{url}"
            response = requests.get(target_url, headers=headers, timeout=15)
            response.raise_for_status()
            text = response.text
            return _clean_text(text)
        except Exception as e:
            # If Reader Mode fails, we'll fall through to standard fetch
            print(f"Reader Mode failed ({str(e)}), falling back to standard fetch...")
            pass

    # 2. Standard BeautifulSoup Fetch (also used for fallback)
    try:
        response = requests.get(url, headers=headers, timeout=12)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
            
        # Get text
        text = soup.get_text()
        return _clean_text(text)
        
    except Exception as e:
        return f"Error fetching URL: {str(e)}"

def _clean_text(text):
    """Internal helper to clean up extracted text."""
    # Break into lines and remove leading/trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # Break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # Drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)
    return text[:10000] # Limit to 10k chars

def _calculate_cost(usage):
    """Calculates estimated cost based on Gemini 2.5 Flash rates."""
    # Rates per 1M tokens
    INPUT_RATE = 0.3
    OUTPUT_RATE = 2.5
    
    input_tokens = usage.prompt_token_count or 0
    output_tokens = usage.candidates_token_count or 0
    
    cost = (input_tokens / 1_000_000 * INPUT_RATE) + (output_tokens / 1_000_000 * OUTPUT_RATE)
    return cost

def generate_linkedin_post(person_text, article_text, person_name):
    """
    Generates a LinkedIn post using Gemini, mimicking the style of person_text.
    Returns a dictionary with result and usage metrics.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"error": "GEMINI_API_KEY not found in environment variables."}

    client = genai.Client(api_key=api_key)
    start_time = time.time()

    prompt = f"""
    You are an expert social media manager and ghostwriter.
    
    I will provide you with two texts:
    1. **Style Reference**: Text written by {person_name}. Analyze their tone, vocabulary, sentence structure, emoji usage, and formatting habits.
    2. **Source Content**: An article or text that needs to be transformed.

    **Your Task**:
    Rewrite the **Source Content** into a high-engagement LinkedIn post that sounds EXACTLY like {person_name}.

    **Style Reference ({person_name})**:
    {person_text[:5000]}

    **Source Content**:
    {article_text[:5000]}

    **Requirements**:
    - Match the persona strictly.
    - Use appropriate LinkedIn formatting (line breaks, bullet points if they use them).
    - Include relevant hashtags if the style reference uses them.
    - Keep it engaging and hook-y.
    - **CRITICAL**: Do NOT have the author introduce themselves (e.g., do NOT say "Hi, I'm {person_name}"). Just dive straight into the value/content.
    - **Emojis**: Use about 4-5 emojis total per post. Use them to qualify the hook/intro line, for bullet points/lists, and a final one at the end. Be playful but use good judgment and taste—it shouldn't feel cluttered, just expressive.
    - **OUTPUT FORMAT**: Output ONLY the post content. Do NOT include any introductory or concluding remarks like "Here is the post" or "Hope this helps". Start directly with the hook.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        duration = time.time() - start_time
        cost = _calculate_cost(response.usage_metadata)
        
        return {
            "text": response.text,
            "duration": duration,
            "cost": cost
        }
    except Exception as e:
        return {"error": f"Error generating post: {str(e)}"}

def refine_linkedin_post(current_post, feedback, person_name):
    """
    Refines an existing LinkedIn post based on user feedback.
    Returns a dictionary with result and usage metrics.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"error": "Error: GEMINI_API_KEY not found."}

    client = genai.Client(api_key=api_key)
    start_time = time.time()

    prompt = f"""
    You are an expert social media manager and ghostwriter for {person_name}.

    **Current Post**:
    {current_post}

    **User Feedback**:
    "{feedback}"

    **Your Task**:
    Rewrite the **Current Post** to address the **User Feedback** while maintaining the voice and style of {person_name}.
    Keep the same formatting rules (no self-intro, thoughtful emojis).
    **OUTPUT FORMAT**: Output ONLY the refined post content. Do NOT include any introductory remarks.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        duration = time.time() - start_time
        cost = _calculate_cost(response.usage_metadata)
        
        return {
            "text": response.text,
            "duration": duration,
            "cost": cost
        }
    except Exception as e:
        return {"error": f"Error refining post: {str(e)}"}
