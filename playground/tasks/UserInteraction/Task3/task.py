import pandas as pd

# Load the dataframe passed from Task 2
dataframe_json = variables.get("dataframe_json")
if not dataframe_json:
    print("Error: No dataframe_json found in variables!")
else:
    print("Dataframe JSON received in Task 3:", dataframe_json)
df = pd.read_json(dataframe_json)

# Display the dataframe
print("Final dataframe:")
print(df)
