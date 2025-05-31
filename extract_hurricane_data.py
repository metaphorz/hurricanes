import pandas as pd

# List of hurricanes we want to extract
hurricanes = [
    {'name': 'IRENE', 'year': 2011},
    {'name': 'ANDREW', 'year': 1992},
    {'name': 'IAN', 'year': 2022},
    {'name': 'IDA', 'year': 2021},
    {'name': 'MILTON', 'year': 2024},
    {'name': 'IDALIA', 'year': 2023},
    {'name': 'HELENE', 'year': 2024}
]

# Load the original large CSV file
print("Loading original CSV file...")
df = pd.read_csv('ibtracs.NA.list.v04r01.csv', skiprows=[1], low_memory=False)

# Create an empty DataFrame to store the extracted data
extracted_data = pd.DataFrame()

# Extract data for each hurricane
print("Extracting hurricane data...")
for hurricane in hurricanes:
    name = hurricane['name']
    year = hurricane['year']
    
    # Filter for the specific hurricane and year
    hurricane_data = df[(df['NAME'].str.upper() == name) & (df['SEASON'] == year)]
    
    if not hurricane_data.empty:
        print(f"Found {len(hurricane_data)} data points for {name} ({year})")
        extracted_data = pd.concat([extracted_data, hurricane_data])
    else:
        print(f"No data found for {name} ({year})")

# Save the extracted data to a new CSV file
output_file = 'hurricane_data_extracted.csv'
print(f"Saving extracted data to {output_file}...")
extracted_data.to_csv(output_file, index=False)

print(f"Extraction complete! Saved {len(extracted_data)} data points for {len(hurricanes)} hurricanes.")
print(f"Original file size: {len(df)} rows")
print(f"New file size: {len(extracted_data)} rows")
print(f"Reduction: {(1 - len(extracted_data)/len(df))*100:.2f}%")
