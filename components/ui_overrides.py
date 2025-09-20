
import streamlit as st

def apply_vv_table_overrides():
    # Prevent transparent/hidden tables under dark themes and ensure scroll area is visible
    st.markdown(
        """
        <style>
        /* Give dataframes a solid background and visible borders */
        .stDataFrame, .stDataFrame [data-testid="stHorizontalBlock"], .stDataFrame div[role="grid"] {
            background-color: #0f1116 !important;
        }
        /* Ensure the dataframe area reserves height and is scrollable */
        div[data-testid="stDataFrame"] div[role="grid"] {
            min-height: 520px !important;
        }
        /* Nudge iframes below to avoid overlapping layers */
        iframe { z-index: 0; }
        </style>
        """,
        unsafe_allow_html=True
    )
