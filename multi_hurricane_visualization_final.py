import pandas as pd
import folium
import numpy as np
from datetime import datetime
import json

# Fix for NumPy int64 JSON serialization issue
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

# Load the smaller extracted CSV file
print("Loading CSV file...")
df = pd.read_csv('hurricane_data_extracted.csv', low_memory=False)

# Convert SEASON to numeric, coercing errors to NaN
df['SEASON'] = pd.to_numeric(df['SEASON'], errors='coerce')

# Define the hurricanes we want to visualize
hurricanes = [
    {'name': 'IRENE', 'year': 2011},
    {'name': 'ANDREW', 'year': 1992},
    {'name': 'IAN', 'year': 2022},
    {'name': 'IDA', 'year': 2021},
    {'name': 'MILTON', 'year': 2024},
    {'name': 'IDALIA', 'year': 2023},
    {'name': 'HELENE', 'year': 2024}
]

# Create a map centered on the Atlantic
hurricane_map = folium.Map(location=[25, -70], zoom_start=4, tiles='CartoDB positron')

# Add US state boundaries
folium.GeoJson(
    'https://raw.githubusercontent.com/python-visualization/folium/master/examples/data/us-states.json',
    name='US States',
    style_function=lambda x: {
        'fillColor': 'transparent',
        'color': 'gray',
        'weight': 1
    }
).add_to(hurricane_map)

# Define colors for hurricane categories
cat_colors = {
    -3: 'gray',     # Not designated
    -2: 'gray',     # Not designated
    -1: 'blue',     # Tropical Depression
    0: 'green',     # Tropical Storm
    1: 'yellow',    # Category 1
    2: 'orange',    # Category 2
    3: 'red',       # Category 3
    4: 'purple',    # Category 4
    5: 'darkred'    # Category 5
}

# Store coordinates for calculating map bounds
all_lats = []
all_lons = []

# Store hurricane information for the info panel
hurricane_info = []

# Process each hurricane
for hurricane in hurricanes:
    print(f"Processing Hurricane {hurricane['name']} ({hurricane['year']})...")
    
    # Filter for this hurricane by name and year
    # Convert to strings to handle any numeric values
    name_matches = df[(df['NAME'].astype(str).str.strip() == hurricane['name']) & 
                      (df['SEASON'].astype(int) == hurricane['year'])]
    
    if len(name_matches) == 0:
        print(f"No exact match found for {hurricane['name']} in {hurricane['year']}")
        # Try a more flexible approach
        name_matches = df[(df['NAME'].astype(str).str.contains(hurricane['name'], case=False, na=False)) & 
                          (df['SEASON'].astype(int) == hurricane['year'])]
    
    # Check if we found any data
    if len(name_matches) == 0:
        print(f"No data found for Hurricane {hurricane['name']} in {hurricane['year']}")
        continue
    
    print(f"Found {len(name_matches)} data points for Hurricane {hurricane['name']}")
    
    # Convert ISO_TIME to datetime for sorting
    hurricane_data = name_matches.copy()
    hurricane_data.loc[:, 'ISO_TIME'] = pd.to_datetime(hurricane_data['ISO_TIME'], errors='coerce')
    
    # Drop rows with invalid dates
    hurricane_data = hurricane_data.dropna(subset=['ISO_TIME'])
    
    # Sort by time
    hurricane_data = hurricane_data.sort_values('ISO_TIME')
    
    if len(hurricane_data) == 0:
        print(f"No valid time data for Hurricane {hurricane['name']}")
        continue
    
    print(f"Date range: {hurricane_data['ISO_TIME'].min()} to {hurricane_data['ISO_TIME'].max()}")
    
    # Extract coordinates
    track_data = hurricane_data[['LAT', 'LON', 'USA_SSHS', 'USA_WIND', 'ISO_TIME']].copy()
    
    # Convert to numeric and drop NaN values
    track_data['LAT'] = pd.to_numeric(track_data['LAT'], errors='coerce')
    track_data['LON'] = pd.to_numeric(track_data['LON'], errors='coerce')
    track_data = track_data.dropna(subset=['LAT', 'LON'])
    
    if len(track_data) == 0:
        print(f"No valid coordinate data for Hurricane {hurricane['name']}")
        continue
    
    coordinates = track_data[['LAT', 'LON']].values.tolist()
    
    # Store coordinates for map bounds
    all_lats.extend(track_data['LAT'].tolist())
    all_lons.extend(track_data['LON'].tolist())
    
    # Get peak intensity for info panel
    max_sshs = pd.to_numeric(track_data['USA_SSHS'], errors='coerce').max()
    peak_category = 'N/A'
    if not pd.isna(max_sshs):
        if max_sshs >= 1:
            peak_category = f'Category {int(max_sshs)}'
        elif max_sshs == 0:
            peak_category = 'Tropical Storm'
        elif max_sshs == -1:
            peak_category = 'Tropical Depression'
        else:
            peak_category = 'Not designated'
    
    # Store hurricane info for the panel
    hurricane_info.append({
        'name': hurricane['name'],
        'year': hurricane['year'],
        'peak': peak_category,
        'start_date': hurricane_data['ISO_TIME'].min().strftime('%B %d, %Y'),
        'end_date': hurricane_data['ISO_TIME'].max().strftime('%B %d, %Y'),
        'max_wind': int(track_data['USA_WIND'].max()) if not pd.isna(track_data['USA_WIND'].max()) else 'N/A'
    })
    
    # Create a full track line with popup containing hurricane info
    popup_html = f"""
    <div style="width:300px; max-height:300px; overflow-y:auto;">
        <h3>{hurricane['name']} ({hurricane['year']})</h3>
        <p><strong>Peak Intensity:</strong> {peak_category}</p>
        <p><strong>Active:</strong> {hurricane_data['ISO_TIME'].min().strftime('%B %d')} - {hurricane_data['ISO_TIME'].max().strftime('%B %d, %Y')}</p>
        <p><strong>Maximum Wind Speed:</strong> {int(track_data['USA_WIND'].max()) if not pd.isna(track_data['USA_WIND'].max()) else 'N/A'} mph</p>
        <p><strong>Description:</strong></p>
        <p>{'Hurricane ' + hurricane['name'] + ' was a powerful ' + ('Category ' + str(int(max_sshs)) if not pd.isna(max_sshs) and max_sshs >= 1 else 'tropical cyclone') + ' that affected ' + ('the Caribbean and U.S. East Coast' if hurricane['name'] == 'IRENE' else 'Florida and the Bahamas' if hurricane['name'] == 'ANDREW' else 'western Cuba and Florida' if hurricane['name'] == 'IAN' else 'Louisiana and the Gulf Coast' if hurricane['name'] == 'IDA' else 'Florida and the Gulf Coast' if hurricane['name'] == 'MILTON' else 'Florida and the Southeast' if hurricane['name'] == 'IDALIA' else 'the Southeast U.S. and Appalachian region')}</p>
    </div>
    """
    
    # Add a thicker, more clickable black line for the entire track with popup
    # Use IFrame for more reliable popup rendering
    iframe = folium.IFrame(html=popup_html, width=320, height=250)
    popup = folium.Popup(iframe, max_width=350)
    
    # Instead of a single PolyLine, create a GeoJson object for better interactivity
    hurricane_track = {
        'type': 'Feature',
        'geometry': {
            'type': 'LineString',
            'coordinates': [[float(coord[1]), float(coord[0])] for coord in coordinates]  # GeoJSON uses [lon, lat] format
        },
        'properties': {
            'name': hurricane['name'],
            'year': int(hurricane['year']),
            'peak': peak_category,
            'start_date': hurricane_data['ISO_TIME'].min().strftime('%B %d, %Y'),
            'end_date': hurricane_data['ISO_TIME'].max().strftime('%B %d, %Y'),
            'max_wind': int(track_data['USA_WIND'].max()) if not pd.isna(track_data['USA_WIND'].max()) else 'N/A'
        }
    }
    
    # Add the track as a GeoJson object with style and popup functions
    folium.GeoJson(
        hurricane_track,
        name=f"{hurricane['name']} {hurricane['year']}",
        style_function=lambda x: {
            'color': 'black',
            'weight': 5,
            'opacity': 0.6,
        },
        tooltip=f"Click for details on {hurricane['name']} ({hurricane['year']})",
        popup=popup
    ).add_to(hurricane_map)
    
    # Create colored line segments based on intensity
    for i in range(len(coordinates) - 1):
        # Get the category and corresponding color
        category = track_data.iloc[i]['USA_SSHS'] if not pd.isna(track_data.iloc[i]['USA_SSHS']) else -3
        color = cat_colors.get(int(category) if not pd.isna(category) else -3, 'gray')
        
        # Get wind speed for tooltip
        wind_speed = track_data.iloc[i]['USA_WIND'] if not pd.isna(track_data.iloc[i]['USA_WIND']) else 'N/A'
        
        # Format date
        date_str = track_data.iloc[i]['ISO_TIME'].strftime('%Y-%m-%d %H:%M')
        
        # Create tooltip text - put storm name first as required
        tooltip_text = f"{hurricane['name']} | {date_str} | Wind: {wind_speed} mph | Lat: {coordinates[i][0]:.2f}, Lon: {coordinates[i][1]:.2f}"
        
        # Create a line segment between consecutive points
        segment = [coordinates[i], coordinates[i+1]]
        
        # Create popup content for this segment
        segment_popup_html = f"""
        <div style="width:250px;">
            <h4>{hurricane['name']} ({hurricane['year']})</h4>
            <p><strong>Date:</strong> {date_str}</p>
            <p><strong>Wind Speed:</strong> {wind_speed} mph</p>
            <p><strong>Category:</strong> {int(category) if not pd.isna(category) and category >= 0 else 'TD/TS' if not pd.isna(category) and category >= -1 else 'Not designated'}</p>
            <p><strong>Location:</strong> {coordinates[i][0]:.2f}°, {coordinates[i][1]:.2f}°</p>
        </div>
        """
        
        # Use IFrame for reliable popup rendering
        segment_iframe = folium.IFrame(html=segment_popup_html, width=270, height=180)
        segment_popup = folium.Popup(segment_iframe, max_width=300)
        
        # Create a GeoJSON feature for this segment
        segment_feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'LineString',
                'coordinates': [[float(segment[0][1]), float(segment[0][0])], [float(segment[1][1]), float(segment[1][0])]]  # GeoJSON uses [lon, lat]
            },
            'properties': {
                'name': hurricane['name'],
                'date': date_str,
                'wind': float(wind_speed) if isinstance(wind_speed, (int, float, np.number)) else wind_speed,
                'category': int(category) if not pd.isna(category) and category >= 0 else 'TD/TS' if not pd.isna(category) and category >= -1 else 'Not designated'
            }
        }
        
        # Add the segment as a colored PolyLine for better visibility of intensity
        # We'll use both approaches: GeoJSON for clickability and PolyLine for coloring
        
        # First add the colored PolyLine (for visual representation)
        folium.PolyLine(
            segment,
            color=color,
            weight=5,
            opacity=0.8,
            tooltip=tooltip_text
        ).add_to(hurricane_map)
        
        # Then add an invisible GeoJson object on top (for better click handling)
        folium.GeoJson(
            segment_feature,
            style_function=lambda x: {
                'color': 'transparent',  # Make it transparent
                'weight': 8,  # Make it wider for easier clicking
                'opacity': 0.0  # Fully transparent
            },
            tooltip=tooltip_text,
            popup=segment_popup
        ).add_to(hurricane_map)
    
    # Add markers for start, middle, and end points
    marker_points = [
        (0, "Start"),
        (len(track_data) // 2, "Middle"),
        (len(track_data) - 1, "End")
    ]
    
    for idx, label in marker_points:
        row = track_data.iloc[idx]
        category = row['USA_SSHS'] if not pd.isna(row['USA_SSHS']) else -3
        color = cat_colors.get(int(category) if not pd.isna(category) else -3, 'gray')
        
        # Create popup content
        date_str = row['ISO_TIME'].strftime('%Y-%m-%d %H:%M')
        wind_speed = row['USA_WIND'] if not pd.isna(row['USA_WIND']) else 'N/A'
        
        popup_text = f"""
        <div>
            <h4>{hurricane['name']} ({hurricane['year']}) - {label} Point</h4>
            <p><strong>Date:</strong> {date_str}</p>
            <p><strong>Location:</strong> {row['LAT']:.2f}°, {row['LON']:.2f}°</p>
            <p><strong>Wind Speed:</strong> {wind_speed} mph</p>
            <p><strong>Category:</strong> {int(category) if not pd.isna(category) and category >= 0 else 'TD/TS' if not pd.isna(category) and category >= -1 else 'Not designated'}</p>
        </div>
        """
        
        # Add marker with IFrame popup for better rendering
        iframe = folium.IFrame(html=popup_text, width=300, height=200)
        popup = folium.Popup(iframe, max_width=300)
        
        folium.CircleMarker(
            location=[row['LAT'], row['LON']],
            radius=8,
            color='black',
            weight=1,
            fill=True,
            fill_color=color,
            fill_opacity=0.9,
            popup=popup,
            tooltip=f"{hurricane['name']} ({hurricane['year']}) - {label}"
        ).add_to(hurricane_map)

# Calculate the bounding box for all hurricanes to set appropriate map view
if all_lats and all_lons:
    southwest = [min(all_lats), min(all_lons)]
    northeast = [max(all_lats), max(all_lons)]
    hurricane_map.fit_bounds([southwest, northeast])

# Add a title
title_html = '''
<div style="position: fixed; 
    top: 10px; left: 50%; transform: translateX(-50%);
    z-index:9999; font-size:18px; font-weight: bold; background-color:white; 
    padding:10px; border-radius:5px; border:1px solid gray; opacity:0.9;">
    Multiple Hurricane Tracks Visualization
</div>
'''
hurricane_map.get_root().html.add_child(folium.Element(title_html))

# Add a legend
legend_html = '''
<div style="position: fixed; 
    bottom: 50px; left: 10px; 
    z-index:9999; font-size:12px; background-color:white; 
    padding:10px; border-radius:5px; border:1px solid gray; opacity:0.9;">
    <div style="font-weight: bold; margin-bottom: 5px;">Hurricane Categories</div>
    <div><span style="background-color:blue; display:inline-block; width:15px; height:15px; margin-right:5px;"></span>Tropical Depression</div>
    <div><span style="background-color:green; display:inline-block; width:15px; height:15px; margin-right:5px;"></span>Tropical Storm</div>
    <div><span style="background-color:yellow; display:inline-block; width:15px; height:15px; margin-right:5px;"></span>Category 1</div>
    <div><span style="background-color:orange; display:inline-block; width:15px; height:15px; margin-right:5px;"></span>Category 2</div>
    <div><span style="background-color:red; display:inline-block; width:15px; height:15px; margin-right:5px;"></span>Category 3</div>
    <div><span style="background-color:purple; display:inline-block; width:15px; height:15px; margin-right:5px;"></span>Category 4</div>
    <div><span style="background-color:darkred; display:inline-block; width:15px; height:15px; margin-right:5px;"></span>Category 5</div>
    <div><span style="background-color:gray; display:inline-block; width:15px; height:15px; margin-right:5px;"></span>Not designated</div>
    <div style="font-style: italic; margin-top: 5px; font-size: 10px;">Click on lines or markers for more information</div>
</div>
'''
hurricane_map.get_root().html.add_child(folium.Element(legend_html))

# Add instructions
instructions_html = '''
<div style="position: fixed; 
    top: 10px; left: 10px; 
    z-index:9999; font-size:12px; background-color:white; 
    padding:10px; border-radius:5px; border:1px solid gray; opacity:0.9;">
    <div style="font-weight: bold; margin-bottom: 5px;">Instructions:</div>
    <div>• Hover over track segments to see basic info</div>
    <div>• Click on any hurricane track or marker for detailed information</div>
    <div>• Colors indicate hurricane intensity category</div>
</div>
'''
hurricane_map.get_root().html.add_child(folium.Element(instructions_html))

# Create the HTML for the information panel with vertical scrolling
info_panel_html = '''
<div style="position: fixed; 
    top: 150px; left: 10px; 
    z-index:9999; font-size:12px; background-color:white; 
    padding:10px; border-radius:5px; border:1px solid gray; opacity:0.9;
    max-height: 35vh; overflow-y: auto; width: 250px;">
    <div style="font-weight: bold; margin-bottom: 10px; text-align: center; font-size: 14px; position: sticky; top: 0; background-color: white; padding: 5px 0;">Hurricane Summary</div>
'''

# Add each hurricane to the info panel
for info in hurricane_info:
    info_panel_html += f'''
    <div style="margin-bottom: 10px; padding-bottom: 5px; border-bottom: 1px solid #eee;">
        <div style="font-weight: bold; color: #333;">{info['name']} ({info['year']})</div>
        <div>Peak Intensity: <span style="color: {'red' if 'Category' in info['peak'] and int(info['peak'].split()[1]) >= 3 else 'orange' if 'Category' in info['peak'] and int(info['peak'].split()[1]) >= 1 else 'green'}">{info['peak']}</span></div>
        <div>Active: {info['start_date']} to {info['end_date']}</div>
        <div>Max Wind: {info['max_wind']} mph</div>
    </div>
    '''

# Add a note about scrolling
info_panel_html += '''
    <div style="font-style: italic; font-size: 10px; text-align: center; margin-top: 5px;">Scroll to see more hurricanes</div>
</div>
'''

# Add the info panel to the map
hurricane_map.get_root().html.add_child(folium.Element(info_panel_html))

# Save the map to an HTML file
output_file = 'multiple_hurricane_tracks_final.html'
# Use our custom NumPy encoder for JSON serialization
folium.GeoJson._get_self_bounds = lambda obj: [[0, 0], [0, 0]]  # Workaround for NumPy serialization issue
folium.GeoJsonTooltip._get_self_bounds = lambda obj: [[0, 0], [0, 0]]  # Workaround for NumPy serialization issue

# Override the default JSON encoder with our NumPy-aware encoder
old_dumps = json.dumps
json.dumps = lambda obj, *args, **kwargs: old_dumps(obj, *args, cls=NumpyEncoder, **kwargs)

# Save the map
hurricane_map.save(output_file)

# Restore the original JSON dumps function
json.dumps = old_dumps

print(f"Map saved to {output_file}")

# Print a completion message with instructions
print("\nVisualization complete! To view the map:")
print(f"1. Open {output_file} in your web browser")
print("2. Hover over track segments to see basic information")
print("3. Click on any hurricane track or marker for detailed information")
print("4. The information panel on the right shows a summary of all hurricanes")
