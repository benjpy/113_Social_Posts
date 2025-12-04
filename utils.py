import os
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def fetch_text_from_url(url):
    """
    Fetches and extracts the main text content from a given URL.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
            
        # Get text
        text = soup.get_text()
        
        # Break into lines and remove leading/trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text[:10000] # Limit to 10k chars to avoid token limits if it's huge
        
    except Exception as e:
        return f"Error fetching URL: {str(e)}"

def generate_linkedin_post(person_text, article_text, person_name):
    """
    Generates a LinkedIn post using Gemini, mimicking the style of person_text.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY not found in environment variables."

    client = genai.Client(api_key=api_key)

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
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error generating post: {str(e)}"

def refine_linkedin_post(current_post, feedback, person_name):
    """
    Refines an existing LinkedIn post based on user feedback.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY not found."

    client = genai.Client(api_key=api_key)

    prompt = f"""
    You are an expert social media manager and ghostwriter for {person_name}.

    **Current Post**:
    {current_post}

    **User Feedback**:
    "{feedback}"

    **Your Task**:
    Rewrite the **Current Post** to address the **User Feedback** while maintaining the voice and style of {person_name}.
    Keep the same formatting rules (no self-intro, thoughtful emojis).
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error refining post: {str(e)}"
