import streamlit as st

# @st.cache_data
def get_error_log():
    # Initialize an empty list for the error log
    if 'error_log' not in st.session_state:
        st.session_state['error_log'] = []
    return st.session_state['error_log']

def log_error(message):
    # Get the cached log, which avoids duplication on reload
    error_log = get_error_log()

    # Append the error message only if it's not already present
    if message not in error_log:
        error_log.append(message)
        st.session_state['error_log'] = error_log  # Save back to session_state


def show():
    st.title("Logging")
    st.write("View the logs of actions performed.")
    # Add logic to display logs
    

    st.title("Logging")

    # Get the error log from cache
    error_log = get_error_log()

    if error_log:
        with st.expander("Error Log", expanded=True):
            for idx, error_msg in enumerate(error_log, 1):
                st.write(f"{idx}. {error_msg}")
    else:
        st.write("No errors logged yet.")    
