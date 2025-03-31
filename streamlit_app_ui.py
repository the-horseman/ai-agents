import streamlit as st
from psycopg_pool import ConnectionPool
from datetime import datetime
import time
import logging
from typing import Dict, List
from langchain_core.messages import HumanMessage
import time
from contextlib import contextmanager
from app.utils.constants import DB_URI
from app.checkpoint.postgres_saver import HumanApprovalPostgresSaver,CheckpointTuple,HumanInputType
from app.graph import create_graph

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Threat Investigation Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'https://your-help-url.com',
        'Report a bug': "https://your-bug-report-url.com",
        'About': "Threat Investigation Dashboard v1.0"
    }
)

# Cache initialization
@st.cache_resource(ttl=300)
def init_resources():
    """Initialize and cache database connection pool and checkpointer"""
    try:
        pool = ConnectionPool(
            conninfo=DB_URI,
            max_size=20,
            kwargs={"autocommit": True, "prepare_threshold": 0}
        )
        checkpointer = HumanApprovalPostgresSaver(pool)
        graph = create_graph(checkpointer)
        return pool, checkpointer, graph
    except Exception as e:
        logger.error(f"Failed to initialize resources: {e}")
        raise

# Initialize resources
pool, checkpointer, graph = init_resources()

@st.cache_data(ttl=30)
def get_pending_tasks():
    return checkpointer.get_pending_inputs()

# Modified caching function
#@st.cache_data(ttl=60)
def get_conversation_history(thread_id: str) -> List[CheckpointTuple]:
    """Conversation history with 60-second TTL"""
    try:
        checkpoints = checkpointer.get_conversation_history(thread_id)
        # Convert to a serializable format
        return checkpoints
    except Exception as e:
        logger.error(f"Error fetching conversation history: {e}")
        return []


def main():
    try:
        load_css()
        # Initialize processing state
        if 'is_processing' not in st.session_state:
            st.session_state.is_processing = False
        if "conversation_history" not in st.session_state:
            st.session_state["conversation_history"] = []
   
        # Header
        st.markdown("""
            <div class='main-header'>
                <h1 style='margin:0;color: #E0E0E0;'>🔍 Threat Investigation Dashboard</h1>
                <p style='margin:0; opacity:0.7;color: #E0E0E0;'>Real-time threat monitoring and analysis</p>
            </div>
        """, unsafe_allow_html=True)

        # Create columns
        col1, col2 = st.columns([1, 4])

        with col1:
            # Add custom CSS for scrollable threat list
            
            st.markdown("""
                <div style='background-color:var(--secondary-bg); padding:1rem; 
                     border-radius:8px; margin-bottom:1rem'>
                    <h3 style='margin:0;color: #E0E0E0;'>📋 Pending Investigations</h3>
                    <p style='margin:0; font-size:0.8em; opacity:0.7;color: #E0E0E0;'>
                        Click on a threat to review
                    </p>
                </div>
            """, unsafe_allow_html=True)
            # Scrollable container for threat cards
            container = st.container(height=1000)
            with container:
                # Get pending investigations
                tasks = get_pending_tasks()
                
                if tasks:
                    # Iterate through inputs and create clickable cards
                    for item in tasks:
                        col1 = st.columns(1)[0]  # Use single column to contain the button
                        with col1:
                            # Determine if this item is currently selected
                            is_selected = ('selected' in st.session_state and 
                                        st.session_state.selected['thread_id'] == item['thread_id'])
                            
                            # If the card is clicked, update the selected item
                            if display_threat_card(item, is_selected):                               
                                st.session_state.selected = item
                                st.session_state.loading_conversation = True
                                st.session_state["conversation_history"] = []                                                          
                                # Force a rerun to update the view
                                st.rerun()

                else:
                    st.info("No pending investigations")
                    
        with col2:
            # Check if a threat is selected in session state
            if "selected" in st.session_state:
                    selected = st.session_state.selected
                
                    # Investigation details header
                    st.markdown(f"""
                                <div style='background-color:var(--secondary-bg); padding:1rem; 
                                    border-radius:8px; margin-bottom:1rem'>
                                    <h3 style='margin:0;color: #E0E0E0;'>
                                        🔎 Investigation Details - {selected['headline'][:500]}...
                                            Severity - {selected['severity']}
                                    </h3>
                                    <p style='margin:0; font-size:1em; opacity:0.7;color: #E0E0E0;'>
                                        Type- {selected['input_type']} | 
                                        Question- {selected['question'].strip().replace('\n', '  \n')[:1000]}...
                                    </p>
                                </div>
                            """, unsafe_allow_html=True)
                        
                    loader = show_loader()
                    # Check if conversation is loading
                    if st.session_state.get('loading_conversation', False):                                                  
                            # Fetch conversation history
                            try:                               
                                msgs = get_conversation_msgs(get_conversation_history(selected['thread_id']))
                                # Update session state
                                last_node = msgs[-1]
                                for msg in msgs:
                                    add_response(msg)
                                if last_node.name and "human_approval" == last_node.name:
                                    last = st.session_state["conversation_history"][-1]
                                    if last.name != "human_approval":
                                        st.session_state["conversation_history"].append(last_node)
                                elif last_node.name and "ask_human" == last_node.name:
                                    last = st.session_state["conversation_history"][-1]
                                    if last.name != "ask_human":
                                        st.session_state["conversation_history"].append(last_node)        
                                st.session_state.loading_conversation = False
                                # Force rerun to display conversation
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error loading conversation: {e}")
                                st.session_state.loading_conversation = False
                                                        
                    # Display conversation if not loading
                    elif 'conversation_history' in st.session_state:
                            display_conversation(st.session_state.conversation_history)

                    display_actions(selected)              
                      
                    st.session_state.is_processing = False
                    hide_loader(loader)           

    
    except Exception as e:
        logger.error(f"Error displaying conversation: ",e)
        st.error("Error displaying conversation. Please try refreshing.")


def format_timestamp(timestamp: datetime) -> str:
    """Format timestamp for display"""
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")


def get_conversation_msgs(checkpoints):
    _msgs_ = []
    for checkpoint_data in checkpoints:
        metadata = checkpoint_data.metadata
        if metadata and metadata['writes']:
            node_key = next(iter(metadata['writes']))
            msgs = metadata['writes'][node_key]
            if "messages" in msgs:
                for msg in msgs["messages"]:
                    _msgs_.append(msg)
    return _msgs_                

# Modified display_conversation function
def display_conversation(msgs: List[CheckpointTuple], page_size: int = 5) -> None:
    """Enhanced conversation display"""
    print(f"display_conversation start , size {len(msgs)}")
    start = time.time()
    try:
        #with st.spinner("Loading conversation history..."):
            timeline = []
            # Process checkpoints
            for msg in msgs:
                if msg.content and msg.type != 'tool':
                    timeline.append({
                                    'node': msg.name if msg.name else "INPUT",
                                    'type': msg.type,
                                    'content': msg.content,
                                })
                       
            for item in timeline:
                with st.chat_message(item['type'].lower()):
                    st.markdown(f"""
                    <div class="scrollable-message">
                        <div class="message-header">{item['node'].upper()}</div>
                        <div class="message-content">{item['content'].replace('\n','  \n')}</div>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                    
            last_node = timeline[-1]

            set_input_type_for_node(last_node)
            end = time.time() - start
            print(f"display_conversation end , time : {end} s")
    except Exception as e:
            logger.error(f"Error displaying conversation:",e)
            st.error("Error displaying conversation. Please try refreshing.") 

def set_input_type_for_node(last_node):
    if last_node['node'] == 'human_approval':
        st.session_state.input_type = "APPROVAL"
    elif last_node['node'] == 'ask_human':
        st.session_state.input_type = "QUESTION"
    else:
        st.session_state.input_type = None           

@contextmanager
def st_chat_container():
    """Context manager for chat container that can be updated"""
    container = st.empty()
    try:
        yield container
    finally:
        pass

def add_response(msg):
    if "conversation_history" in st.session_state :
        if msg not in st.session_state["conversation_history"]:
            st.session_state["conversation_history"].append(msg) 
            return True
    return False    

def process_graph_events(container, input_type, thread_id, user_res):
    """Process and display graph events in real-time"""
    # Prepare graph resumption
    config = {'configurable': {'thread_id': thread_id}}    
    if input_type == 'APPROVAL':
        as_node = "human_approval"
        input_data = {"messages": [HumanMessage(content=user_res,user_approval=user_res)]}
    else:
        as_node = "ask_human"
        input_data = {"messages": [HumanMessage(content=user_res,user_response=user_res)]}
    print(f"process_graph_events start {input_data}, config {config}, input_type{input_type}")   
    # Review the state, decide to edit it, and create a forked checkpoint with the new state     
    state = graph.get_state(config, subgraphs=True)
    # We update the state by passing in the message we want returned from the human node
    graph.update_state(
        state.tasks[0].state.config,
        {"messages": input_data["messages"]},
        as_node=as_node,
    ) 
    interrupt_after=["human_approval","ask_human"]
    for namespace,chunk in graph.stream(None,config,stream_mode="updates",subgraphs=True):
        for node, event in chunk.items():
            if "messages" in event:
                logger.info(f"\n\n{event["messages"][-1].pretty_repr()}\n\n") 
                with container:
                    for msg in event["messages"]:
                        if msg.content and msg.type != 'tool' and add_response(msg):
                            with st.chat_message(msg.type.lower()):
                                st.markdown(f"""
                                <div class="scrollable-message">
                                    <div class="message-header">{msg.name.upper() if msg.name else ""}</div>
                                    <div class="message-content">{msg.content.replace('\n','  \n')}</div>
                                </div>
                                """, 
                                unsafe_allow_html=True
                            )
                    last_msg = event["messages"][-1]            
                    if last_msg and last_msg.content and last_msg.name and last_msg.name in interrupt_after:
                            # Create approval request
                            # Get the latest checkpoint for this thread
                            state = graph.get_state(config, subgraphs=True)
                            cfg = state.tasks[0].state.config
                            print(f"State config {cfg}") 
                            st.session_state.selected['checkpoint_id'] = cfg["configurable"]["checkpoint_id"]
                            st.session_state.input_type = "APPROVAL" if last_msg.name == "human_approval" else "QUESTION"

                            checkpointer.create_input_request(
                                config=cfg,
                                input_type=HumanInputType.APPROVAL if last_msg.name == "human_approval" else HumanInputType.QUESTION,
                                question=last_msg.content,
                                metadata={}
                            )                


def display_threat_card(item: Dict, selected: bool = False) -> bool:
    """Display individual threat card as a button text with enhanced styling"""
    # Severity mapping with colors
    severity_mapping = {
        "s0": {"label": "Unknown", "color": "blue"},
        "s1": {"label": "Info Message", "color": "blue"},
        "s2": {"label": "Medium", "color": "blue"},
        "s3": {"label": "High", "color": "orange"},
        "s4": {"label": "Critical", "color": "red"},
        "s5": {"label": "Fatal", "color": "red"},
        "s6": {"label": "Error Occurred", "color": "voilet"},
    }
    # Determine severity and its color
    severity = item["metadata"].get("severity", "s0").lower()
    severity_label = severity_mapping.get(severity, {"label": "Unknown", "color": "blue"})
    severity_text = severity_label["label"]
    severity_color = severity_label["color"]
    item["headline"] = item["metadata"].get('headline', item['thread_id'])
    item["severity_color"] = severity_color
    item["severity"] = severity_text
    # Prepare button text with threat information
    button_text = (
        f"**Threat**: :{severity_color}[{item["headline"][:200]}...]  \n"
        f"**Severity**: :{severity_color}[{severity_text}]  \n"
        f"**Status**: :orange[{item.get('status', 'PENDING').upper()}]  | "
        f"**Type**: :violet[{item['input_type']}]  \n"
        #f"**Question**: {item['question'].strip().replace('\n', ' ').replace('\r', '')[:150]}...  \n"
        f"**Created**: {format_timestamp(item['created_at'])}"
    )
    
    # Create a unique key for each threat card
    card_key = f"threat_card_{item['thread_id']}"
    
    # Custom CSS to style the button
    st.markdown(f"""
    <style>
    div[data-testid="stButton"] button {{
        background-color: var(--secondary-bg) !important;
        color: var(--text-color) !important;
        border: 1px solid var(--border-color) !important;
        text-align: left !important;
        width: 100% !important;
        padding: 15px !important;
        border-radius: 8px !important;
        white-space: normal !important;
        height: auto !important;
        line-height: 1.6 !important;
        font-size: 0.9em !important;
        margin-bottom: 1px !important;
        transition: all 0.3s ease !important;
    }}
    div[data-testid="stButton"] button:hover {{
        background-color: rgba(44, 44, 44, 0.7) !important;
        border-color: var(--primary-color) !important;
        transform: translateX(5px) !important;
    }}
    div[data-testid="stButton"] button:focus  {{
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 3px rgba(255, 75, 75, 0.3) !important;
    }}
    div[data-testid="stButton"] button.selected  {{
        border-color: var(--primary-color) !important;
        background-color: rgba(255, 75, 75, 0.1) !important;
    }}
    div[data-testid="stButton"] button[data-key="{card_key}"]  {{
                border-color: var(--primary-color) !important;
                background-color: rgba(255, 75, 75, 0.1) !important;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Create the button
    clicked = st.button(button_text, 
                        key=card_key, 
                        use_container_width=True, 
                        type='primary', 
                        help=f"Threat ID: {item['thread_id']}",
                        disabled=st.session_state["is_processing"])
        
    return  clicked



def display_actions(selected):
    if 'input_type' in st.session_state and st.session_state["input_type"]:
        
        if "rejection_reason" not in st.session_state:
                st.session_state["rejection_reason"] = ""
        if "show_confirm" not in st.session_state:
                st.session_state["show_confirm"] = False
        if 'approve_button' in st.session_state and st.session_state.approve_button == True:
                st.session_state.is_processing = True     
        elif 'confirm_reject' in st.session_state and st.session_state.confirm_reject == True:
                st.session_state.is_processing = True    
        elif 'submit_response' in st.session_state and st.session_state.submit_response == True:
                st.session_state.is_processing = True    

        with st_chat_container() as chat_container:
            # Action Header
            st.markdown(
                """
                <div style='background-color:var(--secondary-bg); padding:1rem; 
                    border-radius:8px; margin-top:1rem'>
                    <h4 style='margin:0;color: #E0E0E0;'>Required Action</h4>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Conditionally render actions based on `input_type`
            if st.session_state["input_type"] == "APPROVAL":
                col1, col2 = st.columns(2)
                with col1:
                    # Approve button
                    if st.button(
                        "✅ Approve",
                        key="approve_button",
                        type="primary",
                        disabled=st.session_state.is_processing,
                    ):
                        st.session_state.is_processing = True
                        #loader = show_loader()
                        with st.spinner("Processing approval..."):
                            try:
                                checkpointer.submit_response(
                                    selected["thread_id"],
                                    selected["checkpoint_id"],
                                    "APPROVED",
                                )
                                process_graph_events(
                                    chat_container,
                                    st.session_state["input_type"],
                                    selected["thread_id"],
                                    "APPROVED",
                                )
                                
                            except Exception as e:
                                logger.error(f"Approval error: {e}")
                                st.error("Error processing approval")
                            reset_states()
                            st.rerun()    
                            #hide_loader(loader)
                with col2:
                    # Reject button
                    if st.button(
                        "❌ Reject",
                        key="reject_button",
                        type="secondary",
                        disabled=st.session_state.is_processing,
                    ):
                        st.session_state["show_confirm"] = True

                    if st.session_state["show_confirm"]:
                        st.text_area(
                            "Rejection reason",
                            key="rejection_reason",
                            placeholder="Enter reason for rejection...",
                            height=100,
                            disabled=st.session_state.is_processing,
                        )
                        if st.button(
                            "Confirm Reject",
                            key="confirm_reject",
                            type="primary",
                            disabled=st.session_state.is_processing,
                        ):
                            st.session_state.is_processing = True
                            if st.session_state["rejection_reason"]:
                                #loader = show_loader()
                                with st.spinner("Processing rejection..."):
                                    try:
                                        response = f"Further Investigation needed: {st.session_state['rejection_reason']}"
                                        checkpointer.submit_response(
                                            selected["thread_id"],
                                            selected["checkpoint_id"],
                                            response,
                                        )
                                        process_graph_events(
                                            chat_container,
                                            st.session_state["input_type"],
                                            selected["thread_id"],
                                            response,
                                        )
                                        st.success("Investigation updated!")
                                        
                                    except Exception as e:
                                        logger.error(f"Rejection error: {e}")
                                        st.error("Error processing rejection")
                                        
                                    st.session_state["show_confirm"] = False
                                    reset_states()
                                    #hide_loader(loader)
                                    st.rerun()
            elif st.session_state["input_type"] == "QUESTION":
                # Question Response
                response = st.text_area(
                    "Response",
                    height=100,
                    placeholder="Type your response here...",
                    key="response_input",
                    disabled=st.session_state.is_processing,
                )
                if st.button(
                    "📤 Submit Response",
                    key="submit_response",
                    type="primary",
                    disabled=st.session_state.is_processing,
                ):
                    st.session_state.is_processing = True
                    #loader = show_loader()
                    with st.spinner("Submitting response..."):
                        try:
                            checkpointer.submit_response(
                                selected["thread_id"],
                                selected["checkpoint_id"],
                                response
                            )
                            process_graph_events(
                                chat_container,
                                st.session_state["input_type"],
                                selected["thread_id"],
                                response,
                            )
                            st.success("Response submitted and investigation resumed!")
                            
                        except Exception as e:
                            logger.error(f"Response submission error: {e}")
                            st.error("Error submitting response")
                            
                        reset_states()
                        st.rerun()
                        #hide_loader(loader) 

def reset_states():
    st.session_state.loading_conversation = True
    st.session_state["conversation_history"] = []    
    st.session_state.is_processing = False

def show_loader(message="Processing..."):
    """Show the loader with a message."""
    loader_container = st.empty()
    loader_html = f"""
        <div class="overlay" id="loader-overlay">
            <div class="loader-container">
                <div class="loader"></div>
                <div class="loader-text">{message}</div>
            </div>
        </div>
    """
    loader_container.markdown(loader_html, unsafe_allow_html=True)
    return loader_container

def hide_loader(loader_container):
    """Hide the loader."""
    loader_container.empty()


def load_css():
    st.markdown("""
<style>
     /* Main theme */
    :root {
        --primary-color: #FF4B4B;
        --background-color: #1E1E1E;
        --secondary-bg: #2C2C2C;
        --text-color: #E0E0E0;
        --border-color: #3C3C3C;
    }

    /* Global styles */
    .stApp {
        background-color: var(--background-color);
        color: var(--text-color);
    }
                
    .block-container{
        padding-left: 1rem;
        padding-right: 1rem;
        padding: 3rem 1rem 1rem;   
    }            

    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, var(--secondary-bg), #363636);
        padding: 0.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 5px solid var(--primary-color);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        color:#3C3C3C; 
    }

    /* Card styling */
    .threat-card {
        background-color: var(--secondary-bg);
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        border: 1px solid var(--border-color);
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .threat-card:hover {
        border-color: var(--primary-color);
        transform: translateX(5px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }

    /* Chat container */
    .chat-container {
        background-color: var(--secondary-bg);
        border-radius: 10px;
        padding: 1rem;
        height: calc(100vh - 250px);
        overflow-y: auto;
        box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.1);
    }

    /* Message styling */
    .message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        background-color: #363636;
        animation: fadeIn 0.3s ease;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Status badges */
    .status-badge {
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.8em;
        font-weight: bold;
        display: inline-block;
        text-transform: uppercase;
    }
    .status-pending { background-color: #FFA500; color: black; }
    .status-approved { background-color: #4CAF50; color: white; }
    .status-rejected { background-color: #FF4B4B; color: white; }

    /* Custom button styling */
    .custom-button {
        background-color: var(--primary-color);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        border: none;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .custom-button:hover {
        opacity: 0.9;
        transform: translateY(-2px);
    }

    /* Loading spinner */
    .loading-spinner {
        text-align: center;
        padding: 2rem;
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: var(--background-color);
    }
    ::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #555;
    }        
    .scrollable-message {
        max-height: 300px;
        overflow-y: auto;
        border: 1px solid #ddd;
        padding: 15px;
        border-radius: 8px;
        background-color: #f9f9f9;
        margin: 10px 0;
    }

    .message-header {
        font-size: 1.2em;
        font-weight: bold;
        margin-bottom: 10px;
        color: #2c3e50;
    }

    .message-content {
        font-size: 1em;
        line-height: 1.5;
        color: #34495e;
    }

    /* Customize scrollbar */
    .scrollable-message::-webkit-scrollbar {
        width: 8px;
    }

    .scrollable-message::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }

    .scrollable-message::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 4px;
    }

    .scrollable-message::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
    .main-header * {
        color: #E0E0E0;
    }        
    .overlay-loader {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.6);
            z-index: 1000;
            display: none;  /* Hidden by default */
            align-items: center;
            justify-content: center;
        }
        .loader-text {
            font-size: 1.5rem;
            color: white;
            font-weight: bold;
        }
        
        /* Overlay */
            .overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 1000;
                opacity: 1;
                transition: opacity 0.3s ease-in-out;
            }
            
            .overlay.hidden {
                opacity: 0;
                pointer-events: none;
            }
            
            /* Loader */
            .loader-container {
                background: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            
            .loader {
                width: 48px;
                height: 48px;
                border: 5px solid #FFF;
                border-bottom-color: #FF3D00;
                border-radius: 50%;
                display: inline-block;
                box-sizing: border-box;
                animation: rotation 1s linear infinite;
            }

            @keyframes rotation {
                0% {
                    transform: rotate(0deg);
                }
                100% {
                    transform: rotate(360deg);
                }
            }
            
            .loader-text {
                margin-top: 10px;
                color: #333;
                font-size: 14px;
                font-weight: 500;
            }
    .threat-list-container {
        max-height: 600px;
        overflow-y: auto;
        padding: 10px;
        border: 1px solid #333;
        border-radius: 8px;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        padding: 0.1px;          
    }
    div[data-testid="stVerticalBlock"]{
        gap: 0.3rem;  
    }                   
</style>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()