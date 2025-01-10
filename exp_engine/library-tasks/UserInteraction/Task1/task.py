import pandas as pd

# Create a simple dataframe
data = {'Name': ['Alice', 'Bob', 'Charlie'], 'Age': [25, 30, 35]}
df = pd.DataFrame(data)

# Save the dataframe to a JSON string to pass it to the next task
variables.put("dataframe_json", df.to_json())
print("Dataframe created and passed to Task 2.")
