import pandas as pd
import numpy as np

# 1. Define the URL for the E. coli Promoter dataset
url = 'https://archive.ics.uci.edu/ml/machine-learning-databases/molecular-biology/promoter-gene-sequences/promoters.data'

# 2. Define column names (The raw data doesn't have headers)
# 'Class' = + (Promoter) or - (Non-promoter)
# 'id' = Instance ID
# 'Sequence' = The actual DNA string
names = ['Class', 'id', 'Sequence']

# 3. Read the data using Pandas
data = pd.read_csv(url, names=names)

# 4. Clean up: The dataset can be a bit messy. Let's inspect it.
print(f"Dataset Shape: {data.shape}")
print("\n--- First 5 Rows ---")
print(data.head())

# 5. Check for valid DNA characters
# We want to make sure we only have A, T, C, G
print("\n--- Data Types ---")
print(data.dtypes)