import streamlit as st
import utils
import os

# Page Config
st.set_page_config(
    page_title="LinkedIn Ghostwriter",
    page_icon="✍️",
    layout="centered"
)

# Load Custom CSS
def load_css():
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Header
st.title("✍️ LinkedIn Ghostwriter")
st.markdown("""
    <p style='font-size: 1.1rem; color: #666; margin-bottom: 2rem;'>
        Transform any article into a viral LinkedIn post, written in the exact style of your favorite creator.
    </p>
""", unsafe_allow_html=True)

# Main Input Area
with st.container():
    col1, col2 = st.columns(2)
    
    # Define Persona Mapping
    PERSONA_MAP = {
        "SOSV ([link](https://raw.githubusercontent.com/benjpy/113_Social_Posts/main/sosv.txt))": "sosv.txt",
        "Sean O'Sullivan ([link](https://raw.githubusercontent.com/benjpy/113_Social_Posts/main/sean.txt))": "sean.txt",
        "Po Bronson ([link](https://raw.githubusercontent.com/benjpy/113_Social_Posts/main/po.txt))": "po.txt"
    }

    with col1:
        st.subheader("1. Select Persona")
        persona_choice = st.radio(
            "Select Persona",
            options=list(PERSONA_MAP.keys()),
            help="Choose a writing style.",
            label_visibility="collapsed"
        )

    with col2:
        st.subheader("2. The Content")
        article_url = st.text_input(
            "Source Article URL",
            placeholder="e.g. https://techcrunch.com/...",
            help="URL to the article you want to rewrite."
        )
        st.write("") # Add a little spacing
        generate_btn = st.button("✨ Generate Post")

# Logic
if generate_btn:
    if not article_url:
        st.error("Please provide the Source Article URL.")
    elif not os.getenv("GEMINI_API_KEY"):
        st.error("⚠️ GEMINI_API_KEY not found. Please check your .env file.")
    else:
        with st.spinner("🔍 Reading persona and content..."):
            # Determine file to read from mapping
            filename = PERSONA_MAP.get(persona_choice)
            
            # Read persona file
            try:
                with open(filename, "r") as f:
                    person_text = f.read()
            except FileNotFoundError:
                st.error(f"Error: Could not find {filename}. Please ensure it exists in the project directory.")
                st.stop()

            # Fetch article content
            article_text = utils.fetch_text_from_url(article_url)
            
            if "Error" in article_text:
                st.error(f"Could not read Source URL: {article_text}")
            else:
                # Generate
                with st.spinner(f"🤖 Crafting post in {persona_choice}'s style..."):
                    post_content = utils.generate_linkedin_post(person_text, article_text, persona_choice)
                    
                    if "Error" in post_content:
                        st.error(post_content)
                    else:
                        st.session_state.post_content = post_content
                        st.session_state.persona_choice = persona_choice # Store for refinement
                        st.success("Post generated successfully!")

# Display Post if it exists in session state
if "post_content" in st.session_state:
    st.subheader("Your Draft")
    
    # Styled container for the post (Light theme, wrapped text)
    # We use st.code because it has a native "Copy" button in the top right.
    # We have overridden the CSS for .stCode in style.css to make it look like normal text (sans-serif, wrapped).
    st.code(st.session_state.post_content, language=None)

    st.markdown("---")
    st.subheader("Refine this post")
    
    feedback = st.text_input(
        "Are you happy with the result? What should I change?",
        placeholder="e.g. Make it shorter, add more emojis, make it punchier..."
    )
    
    if st.button("🔄 Refine Post"):
        if not feedback:
            st.warning("Please enter some feedback first.")
        else:
            with st.spinner("🤖 Refining your post..."):
                refined_post = utils.refine_linkedin_post(
                    st.session_state.post_content, 
                    feedback, 
                    st.session_state.get("persona_choice", "Sean O'Sullivan")
                )
                
                if "Error" in refined_post:
                    st.error(refined_post)
                else:
                    st.session_state.post_content = refined_post
                    st.rerun()

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #888; font-size: 0.9rem;'>Powered by Google Gemini 2.0 Flash</div>",
    unsafe_allow_html=True
)
