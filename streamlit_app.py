import streamlit as st
from llama_index.llms.gemini import Gemini
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.embeddings.gemini import GeminiEmbedding


st.set_page_config(page_title="Chat with an expert on the works of Library Personas", page_icon="🦙", layout="centered", initial_sidebar_state="auto", menu_items=None)
st.title("Chat with an export on the works of Library Personas ")
st.info("Check out the full tutorial to build this app in our [blog post](https://blog.streamlit.io/build-a-chatbot-with-custom-data-sources-powered-by-llamaindex/)", icon="📃")

if "messages" not in st.session_state.keys():  # Initialize the chat messages history
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Ask me a question about Library Personas!",
        }
    ]

@st.cache_resource(show_spinner=False)
def load_data():
    reader = SimpleDirectoryReader(input_dir="./data", recursive=True)
    docs = reader.load_data()

    Settings.chunk_size = 1500
    Settings.chunk_overlap = 50
    Settings.embed_model = GeminiEmbedding()
    
    Settings.llm = Gemini(
        model="models/gemini-1.5-flash",
        temperature=0.2,
        system_prompt="""You are a an expert on the work of library personaS
        Answer the question using the provided documents, which contain relevant excerpts from the work of THESE articles
       Whenver possible, include a quotation from the provided excerpts of his work to illustrate your point.
        Respond using a florid but direct tone, typical of an early modernist writer.
        Keep your answers under 200 words. make sure to use emojis when appicable.""",
        api_key = st.secrets.google_gemini_key,
        safe = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_ONLY_HIGH",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_ONLY_HIGH",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_ONLY_HIGH",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_ONLY_HIGH",
    },
],
    )
 

    index = VectorStoreIndex.from_documents(docs)
    return index


index = load_data()

if "chat_engine" not in st.session_state.keys():  # Initialize the chat engine
    st.session_state.chat_engine = index.as_chat_engine(
        chat_mode="condense_plus_context", verbose=True, streaming=False,
    )

if prompt := st.chat_input(
    "Ask a question"
):  # Prompt for user input and save to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

for message in st.session_state.messages:  # Write message history to UI
    with st.chat_message(message["role"]):
        st.write(message["content"])

# If last message is not from assistant, generate a new response
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        response_stream = ""
        try:
            response_stream = st.session_state.chat_engine.stream_chat(prompt)
        except:
            st.error("We got an error from Google Gemini - this may mean the question had a risk of producing a harmful response. Consider asking the question in a different way.")        
        if response_stream != "":
            with st.spinner("waiting"):
                try:
                    st.write_stream(response_stream.response_gen)
                except:
                    st.error("We hit a bump - let's try again")
                    try:
                        resp = st.session_state.chat_engine.chat(prompt)[0]
                        st.write(resp)
                    except:
                        st.error("We got an error from Google Gemini - this may mean the question had a risk of producing a harmful response. Consider asking the question in a different way.")
            message = {"role": "assistant", "content": response_stream.response}
            # Add response to message history
            st.session_state.messages.append(message)
