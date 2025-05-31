# Multi-Hurricane Track Visualization

## Overview
This project creates an interactive visualization of multiple hurricane tracks using Python and Folium. The visualization displays the paths of seven significant hurricanes (Irene 2011, Andrew 1992, Ian 2022, Ida 2021, Milton 2024, Idalia 2023, and Helene 2024) with color-coded intensity segments based on the Saffir-Simpson hurricane scale.

## Features
- Interactive map showing all seven hurricane tracks simultaneously
- Color-coded line segments representing hurricane intensity categories
- Tooltips showing hurricane name, date/time, wind speed, and location
- Detailed popups when clicking on hurricane tracks or markers
- Markers at the start, middle, and end points of each track
- Legend explaining the color coding
- Scrollable information panel listing all hurricanes with their peak intensities
- Optimized data processing using a pre-extracted dataset

## Requirements
- Python 3.x
- pandas
- numpy
- folium
- datetime

## Data Source
The visualization uses data from the International Best Track Archive for Climate Stewardship (IBTrACS) dataset. To optimize performance and repository size, we've extracted only the relevant hurricane data using the `extract_hurricane_data.py` script, which creates a much smaller `hurricane_data_extracted.csv` file containing only the data for the seven hurricanes of interest.

## Usage
1. Ensure you have all required dependencies installed
2. If needed, run the data extraction script: `python extract_hurricane_data.py` (this step is optional as the extracted data file is included)
3. Run the visualization script: `python multi_hurricane_visualization_final.py`
4. Open the generated HTML file (`multiple_hurricane_tracks_final.html`) in a web browser

## Interacting with the Visualization
- Hover over track segments to see basic information
- Click on any hurricane track or marker for detailed information
- Use the scrollable information panel on the left to see a summary of all hurricanes
- Refer to the legend to understand the color coding of hurricane categories

## Files
- `multi_hurricane_visualization_final.py`: Main script to generate the visualization
- `extract_hurricane_data.py`: Script to extract relevant hurricane data from the large source file
- `hurricane_data_extracted.csv`: Smaller dataset containing only the relevant hurricane data
- `multiple_hurricane_tracks_final.html`: Output visualization file
- `.gitignore`: Configuration to exclude large files from version control
- `Requirements.txt`: Project requirements and specifications

## Improvements
- **Data Optimization**: Reduced dataset size by 99.58% (from 126,838 rows to 537 rows) by extracting only relevant hurricane data
- **Enhanced Interactivity**: Improved popup reliability by using IFrame and GeoJSON for better rendering
- **UI Improvements**: Added vertical scrolling to the hurricane summary box to accommodate multiple hurricanes
- **Layout Optimization**: Adjusted positioning of information panels to avoid overlap and improve readability
- **Performance**: Fixed NumPy serialization issues for smoother rendering and better compatibility
- **Version Control**: Added proper .gitignore configuration to exclude large files
