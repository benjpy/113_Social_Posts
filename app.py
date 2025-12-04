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
    
    with col1:
        st.subheader("1. The Persona")
        person_name = st.text_input(
            "Person's Name",
            placeholder="e.g. Paul Graham",
            help="Name of the person whose style you want to mimic."
        )
        person_url = st.text_input(
            "Profile or Blog URL",
            placeholder="e.g. https://paulgraham.com/articles.html",
            help="URL to a page with text written by the person you want to mimic."
        )

    with col2:
        st.subheader("2. The Content")
        article_url = st.text_input(
            "Source Article URL",
            placeholder="e.g. https://techcrunch.com/...",
            help="URL to the article you want to rewrite."
        )

    generate_btn = st.button("✨ Generate Post")

# Logic
if generate_btn:
    if not person_url or not article_url or not person_name:
        st.error("Please provide Name, Persona URL, and Article URL.")
    elif not os.getenv("GEMINI_API_KEY"):
        st.error("⚠️ GEMINI_API_KEY not found. Please check your .env file.")
    else:
        with st.spinner("🔍 Analyzing style and reading content..."):
            # Fetch content
            person_text = utils.fetch_text_from_url(person_url)
            article_text = utils.fetch_text_from_url(article_url)
            
            if "Error" in person_text:
                st.error(f"Could not read Persona URL: {person_text}")
            elif "Error" in article_text:
                st.error(f"Could not read Source URL: {article_text}")
            else:
                # Generate
                with st.spinner(f"🤖 Crafting post in {person_name}'s style..."):
                    post_content = utils.generate_linkedin_post(person_text, article_text, person_name)
                    
                    if "Error" in post_content:
                        st.error(post_content)
                    else:
                        st.success("Post generated successfully!")
                        st.subheader("Your Draft")
                        st.text_area("Copy your post below:", value=post_content, height=400)
                        st.balloons()

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #888; font-size: 0.9rem;'>Powered by Google Gemini 2.0 Flash</div>",
    unsafe_allow_html=True
)
