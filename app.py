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

# Initialize Session State
if "total_cost" not in st.session_state:
    st.session_state.total_cost = 0.0

# Header
st.title("✍️ LinkedIn Ghostwriter")
st.markdown("""
    <p style='font-size: 1.1rem; color: #666; margin-bottom: 2rem;'>
        Transform any article into a LinkedIn post using preset styles.
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
        input_tab1, input_tab2 = st.tabs(["🔗 URL", "📝 Text"])
        
        with input_tab1:
            article_url = st.text_input(
                "Source Article URL",
                placeholder="e.g. https://techcrunch.com/...",
                help="URL to the article you want to rewrite.",
                label_visibility="collapsed"
            )
            use_reader = st.checkbox("Use Reader Mode (bypasses consent windows)", value=True, help="Uses Jina Reader to extract clean text from URLs that might have consent windows.")
        
        with input_tab2:
            raw_text = st.text_area(
                "Paste Article Text",
                placeholder="Paste the article content here...",
                help="Paste the full text of the article you want to rewrite.",
                height=150,
                label_visibility="collapsed"
            )
            
        st.write("") # Add a little spacing
        generate_btn = st.button("✨ Generate Post")

# Logic
if generate_btn:
    if not os.getenv("GEMINI_API_KEY"):
        st.error("⚠️ GEMINI_API_KEY not found. Please check your .env file.")
    else:
        with st.spinner("🔍 Preparing content..."):
            # Determine file to read from mapping
            filename = PERSONA_MAP.get(persona_choice)
            
            # Read persona file
            try:
                with open(filename, "r") as f:
                    person_text = f.read()
            except FileNotFoundError:
                st.error(f"Error: Could not find {filename}. Please ensure it exists in the project directory.")
                st.stop()

            # Process Content
            article_text = ""
            if raw_text.strip():
                article_text = raw_text.strip()
            elif article_url.strip():
                article_text = utils.fetch_text_from_url(article_url, use_reader=use_reader)
            else:
                st.error("Please provide either a Source URL or paste the Article Text.")
                st.stop()
            
            if not article_text or "Error" in article_text:
                st.error(f"Could not process content: {article_text if article_text else 'No content found'}")
                st.info("💡 **Tip**: If the URL is blocked or restricted, try copying the article text and pasting it directly into the **📝 Text** tab above.")
            else:
                # Generate
                with st.spinner(f"🤖 Crafting post in {persona_choice}'s style..."):
                    result = utils.generate_linkedin_post(person_text, article_text, persona_choice)
                    
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.session_state.post_content = result["text"]
                        st.session_state.duration = result["duration"]
                        st.session_state.cost = result["cost"]
                        st.session_state.total_cost += result["cost"]
                        st.session_state.persona_choice = persona_choice # Store for refinement
                        st.success("Post generated successfully!")

# Display Post if it exists in session state
if "post_content" in st.session_state:
    st.subheader("Your Draft")
    
    # Display metrics
    if "duration" in st.session_state and "cost" in st.session_state:
        st.caption(f"⏱️ {st.session_state.duration:.1f}s | 💸 Est. cost: ${st.session_state.cost:.5f} (Total Session: ${st.session_state.total_cost:.5f})")
    
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
                result = utils.refine_linkedin_post(
                    st.session_state.post_content, 
                    feedback, 
                    st.session_state.get("persona_choice", "Sean O'Sullivan")
                )
                
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.session_state.post_content = result["text"]
                    st.session_state.duration = result["duration"]
                    st.session_state.cost = result["cost"]
                    st.session_state.total_cost += result["cost"]
                    st.rerun()

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #888; font-size: 0.9rem;'>Powered by Google Gemini 2.5 Flash</div>",
    unsafe_allow_html=True
)
