import pandas as pd

# (Paste the loading code from the previous step here if this is a new file)
# OR assume 'data' variable exists from previous step
url = 'https://archive.ics.uci.edu/ml/machine-learning-databases/molecular-biology/promoter-gene-sequences/promoters.data'
names = ['Class', 'id', 'Sequence']
data = pd.read_csv(url, names=names)

print("--- 1. Cleaning Data ---")

# Step A: Remove the tab characters (\t) from the Sequence column
data['Sequence'] = data['Sequence'].str.replace('\t', '')

# Step B: Split the 'Sequence' string into individual characters
# This creates a list of characters for each row
sequence_list = data['Sequence'].apply(list).tolist()

# Step C: Create a new DataFrame where each letter is a separate column
# There are 57 bases in each sequence, so we get 57 columns
new_df = pd.DataFrame(sequence_list)

# Step D: Add the Class label back
new_df['Class'] = data['Class']

# Step E: Rename columns to be meaningful
# 0 -> 'p1', 1 -> 'p2', ... (p stands for position)
new_df.columns = [f'p{i+1}' for i in range(len(new_df.columns)-1)] + ['Class']

# Move 'Class' column to the front for easier reading
cols = ['Class'] + [col for col in new_df.columns if col != 'Class']
new_df = new_df[cols]

print("✅ Data Cleaned and Restructured!")
print(f"New Shape: {new_df.shape}")
print("\n--- First 5 Rows (Cleaned) ---")
print(new_df.iloc[:5, :10]) # Showing only first 10 columns to keep it readable

# ==========================================
# PHASE 4 PART 2: NUMERICAL ENCODING
# ==========================================
from sklearn.model_selection import train_test_split

print("\n--- 2. Numerical Encoding ---")

# Step A: Encode the 'Class' column (Target)
# + becomes 1, - becomes 0
y = new_df['Class'].apply(lambda x: 1 if x == '+' else 0)

# Step B: Encode the DNA Sequence columns (Features)
# We drop 'Class' first because we already saved it in 'y'
X = new_df.drop('Class', axis=1)

# This converts 'p1_a', 'p1_c', 'p1_g', 'p1_t' into 1s and 0s
X = pd.get_dummies(X)

print(f"Original Shape: {new_df.shape}")
print(f"Encoded Shape:  {X.shape}") 
# You should see (106, 228) because 57 positions * 4 letters = 228 columns

# Step C: Split into Training and Testing sets
# 75% for training the AI, 25% for testing it later
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

print("\n✅ Data Ready for AI!")
print(f"Training Data: {X_train.shape}")
print(f"Testing Data:  {X_test.shape}")




# ==========================================
# PHASE 5: BUILDING THE NEURAL NETWORK
# ==========================================
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

print("\n--- 3. Training the Neural Network ---")

# Step A: Initialize the Brain
# hidden_layer_sizes=(100, 50): Two layers of neurons.
# max_iter=1000: The AI will study the data 1000 times (epochs).
model = MLPClassifier(hidden_layer_sizes=(100, 50), max_iter=1000, activation='relu', solver='adam', random_state=42)

# Step B: Train the model (The Learning Phase)
print("Training in progress...")
model.fit(X_train, y_train)
print("✅ Training Complete!")

# Step C: Test the model
# We hide the answers (y_test) and ask the model to guess based on X_test
predictions = model.predict(X_test)

# Step D: Evaluate Performance
accuracy = accuracy_score(y_test, predictions)
print(f"\n🎯 Model Accuracy: {accuracy * 100:.2f}%")

print("\n--- Detailed Report ---")
print(classification_report(y_test, predictions))

print("\n--- Confusion Matrix ---")
# [True Negative, False Positive]
# [False Negative, True Positive]
print(confusion_matrix(y_test, predictions))



# ==========================================
# PHASE 6: SAVING THE MODEL
# ==========================================
import pickle

print("\n--- 4. Saving the Model ---")

# We need to save the Model AND the Column Names.
# Why? When a user types "ATCG", we need to format it exactly like the training data.
model_data = {
    'model': model,
    'model_columns': X_train.columns
}

filename = 'gene_model.pkl'
with open(filename, 'wb') as file:
    pickle.dump(model_data, file)

print(f"✅ Model saved to '{filename}'")
print("You are ready to build the Website/UI!")