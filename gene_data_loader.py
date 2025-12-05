import pandas as pd
import numpy as np

# 1. Define the URL for the E. coli Promoter dataset
url = 'https://archive.ics.uci.edu/ml/machine-learning-databases/molecular-biology/promoter-gene-sequences/promoters.data'

# 2. Define column names
names = ['Class', 'id', 'Sequence']

# 3. Read the data
try:
    data = pd.read_csv(url, names=names)
    print("✅ SUCCESS: Data loaded from UCI Repository!")
    
    # 4. Show the shape
    print(f"Dataset Shape: {data.shape}")
    
    # 5. Show the first 5 rows (The messy raw data)
    print("\n--- First 5 Rows (Raw) ---")
    print(data.head())

except Exception as e:
    print(f"❌ ERROR: Could not load data. Check your internet connection.\nError details: {e}")


    