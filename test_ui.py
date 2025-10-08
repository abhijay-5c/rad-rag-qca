import streamlit as st

st.title("Test UI - Navigation Check")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Choose a page", [
    "Search", 
    "Browse by Study", 
    "Database Statistics",
    "Case Input",
    "Interactive Checklist",
    "Report Generation",
    "Report History"
])

st.write(f"Current page: {page}")

if page == "Search":
    st.header("🔍 Search CT Study Chunks")
    st.write("This is the Search page")

elif page == "Case Input":
    st.header("📝 Case Input")
    st.write("This is the Case Input page")

elif page == "Interactive Checklist":
    st.header("📋 Interactive Checklist")
    st.write("This is the Interactive Checklist page")

elif page == "Report Generation":
    st.header("📄 Report Generation")
    st.write("This is the Report Generation page")

elif page == "Report History":
    st.header("📚 Report History")
    st.write("This is the Report History page")

else:
    st.write(f"This is the {page} page")
