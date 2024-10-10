import streamlit as st
import os
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Initialize session state variables
if 'step' not in st.session_state:
    st.session_state.step = 'choose_category'
    st.session_state.liked_jokes = []
    st.session_state.disliked_jokes = []
    st.session_state.current_jokes = []

def generate_jokes(category, liked_jokes, disliked_jokes):
    prompt = f"""Generate 4 jokes in the {category} category. 
    These are the previous jokes the user liked: {liked_jokes}
    These are the previous jokes the user disliked: {disliked_jokes}
    Return only the jokes, one per line, without numbering or any other text."""
    
    messages = [
        {"role": "system", "content": "You are a comedian specialized in generating jokes based on user preferences."},
        {"role": "user", "content": prompt}
    ]

    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages
    )

    # Filter out empty lines and strip whitespace
    return [joke.strip() for joke in response.choices[0].message.content.strip().split('\n') if joke.strip()]

def generate_explanation(joke):
    prompt = f"Explain this joke briefly: {joke}"
    messages = [
        {"role": "system", "content": "You're a concise joke explainer."},
        {"role": "user", "content": prompt}
    ]
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    return response.choices[0].message.content.strip()

# Streamlit UI
st.title("AI Joke Generator Game")

if st.session_state.step == 'choose_category':
    st.subheader("Choose your preferred humor category:")
    categories = ["Dark Humor", "Puns", "Dad Jokes", "Sarcasm", "Observational"]
    category = st.selectbox("Select a category", categories)
    if st.button("Start Game"):
        st.session_state.category = category
        st.session_state.step = 'generate_jokes'
        st.rerun()

elif st.session_state.step == 'generate_jokes':
    st.session_state.current_jokes = generate_jokes(
        st.session_state.category, 
        st.session_state.liked_jokes, 
        st.session_state.disliked_jokes
    )
    st.session_state.step = 'rate_jokes'
    st.rerun()

elif st.session_state.step == 'rate_jokes':
    st.subheader("Choose the funniest joke:")
    for i, joke in enumerate(st.session_state.current_jokes):
        if st.button(joke, key=f"like_{i}", use_container_width=True):
            st.session_state.liked_jokes.append(joke)
            st.session_state.current_jokes.pop(i)
            st.session_state.step = 'dislike_joke'
            st.rerun()
        
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button("Explain", key=f"explain_{i}"):
                explanation = generate_explanation(joke)
                st.info(explanation, icon="ℹ️")
    
    if st.button("None are funny", key="no_funny"):
        st.session_state.step = 'dislike_joke'
        st.rerun()

elif st.session_state.step == 'dislike_joke':
    st.subheader("Now choose the least funny joke:")
    for i, joke in enumerate(st.session_state.current_jokes):
        if st.button(joke, key=f"dislike_{i}", use_container_width=True):
            st.session_state.disliked_jokes.append(joke)
            st.session_state.step = 'generate_jokes'
            st.rerun()
        
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button("Explain", key=f"explain_dislike_{i}"):
                explanation = generate_explanation(joke)
                st.info(explanation, icon="ℹ️")

    if st.button("They're all funny", key="no_unfunny"):
        st.session_state.step = 'generate_jokes'
        st.rerun()

    st.write("Liked jokes:", len(st.session_state.liked_jokes))
    st.write("Disliked jokes:", len(st.session_state.disliked_jokes))

    if st.button("End Game"):
        st.session_state.step = 'game_over'
        st.rerun()

elif st.session_state.step == 'game_over':
    st.subheader("Game Over")
    st.write("Thanks for playing! Here are your results:")
    st.write("Liked jokes:", len(st.session_state.liked_jokes))
    st.write("Disliked jokes:", len(st.session_state.disliked_jokes))
    
    if st.button("Play Again"):
        st.session_state.step = 'choose_category'
        st.session_state.liked_jokes = []
        st.session_state.disliked_jokes = []
        st.session_state.current_jokes = []
        st.rerun()