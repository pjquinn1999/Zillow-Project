import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

st.title("Zillow Housing Data")
folder_path = "zillow_data"

try:
    files = os.listdir(folder_path)
    files = [f for f in files if os.path.isfile(os.path.join(folder_path, f)) and f.endswith('.csv')]
except Exception as e:
    st.error(f"Error accessing folder: {e}")
    files = []

if files:
    selected_file = st.selectbox("Select a CSV file", files)
    
    if selected_file:
        try: 
            file_path = os.path.join(folder_path, selected_file)
            df = pd.read_csv(file_path)
        
            st.subheader(f"Preview of {selected_file}")
            st.write(df.head())
        
            # Select columns to plot
            columns = df.columns.tolist()
        
            x_col = st.selectbox("Select X-axis column", columns, key="x_axis")
            y_col = st.selectbox("Select Y-axis column", columns, key="y_axis")
        
            if st.button("Plot Graph"):
                fig, ax = plt.subplots()
                ax.plot(df[x_col], df[y_col], marker='o')
                ax.set_xlabel(x_col)
                ax.set_ylabel(y_col)
                ax.set_title(f"{y_col} vs {x_col}")
                st.pyplot(fig)

        except Exception as e:
            st.error(f"Error loading or processing file: {e}")

else:
    st.info(f"No CSV files found in the folder: {folder_path}")



