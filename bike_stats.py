import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import logging

# Set up logging
logging.basicConfig(filename='cyclist_accidents.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Load the dataset from CSV file
df = pd.read_csv('cyclist_accidents.csv')

# Convert 'Date' to datetime format
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')  # Handle invalid dates

# Convert 'Time' to datetime, using format '%H:%M:%S' to match the data
df['Time'] = pd.to_datetime(df['Time'], format='%H:%M:%S', errors='coerce')

# Drop rows where 'Time' is NaT (invalid/missing)
df_clean = df.dropna(subset=['Time'])

# Extract the hour from 'Time'
df_clean['Hour'] = df_clean['Time'].dt.hour

# Create the 'DayOfWeek' column based on 'Date'
df_clean['DayOfWeek'] = df_clean['Date'].dt.day_name()

# Check for missing values in key columns after cleaning
missing_values = df_clean[['Cyclists Injured', 'Cyclists Killed', 'Hour', 'DayOfWeek', 'Borough']].isnull().sum()
logging.debug("\nMissing values in key columns after cleaning:")
logging.debug(missing_values)

# Log a sample of the clean dataset to verify the data
logging.debug("\nSample of cleaned data:")
logging.debug(df_clean[['Date', 'Time', 'Hour', 'DayOfWeek', 'Borough', 'Cyclists Injured', 'Cyclists Killed']].head(10))

# Calculate the 'Chances of Death or Injury'
total_injuries_deaths = df_clean.groupby(['DayOfWeek', 'Hour'])[['Cyclists Injured', 'Cyclists Killed']].sum()
total_events_by_day_hour = df_clean.groupby(['DayOfWeek', 'Hour']).size()
chances_of_injury_or_death = total_injuries_deaths.sum(axis=1) / total_events_by_day_hour

# Merge the chances back into the original dataframe
df_clean = df_clean.merge(chances_of_injury_or_death.reset_index(name='Chances of Death or Injury'),
                          on=['DayOfWeek', 'Hour'], how='left')

# Save the updated DataFrame to a new CSV file
df_clean.to_csv('cyclist_accidents_with_chances.csv', index=False)

# Log success message
logging.debug("Updated DataFrame with 'Chances of Death or Injury' column has been saved to 'cyclist_accidents_with_chances.csv'.")

# Group by 'Hour' and aggregate injuries and deaths
injuries_by_hour = df_clean.groupby('Hour')[['Cyclists Injured', 'Cyclists Killed']].sum()
logging.debug("\nInjuries by Hour (aggregated):")
logging.debug(injuries_by_hour)

# Group by 'DayOfWeek' and aggregate injuries and deaths
injuries_by_day = df_clean.groupby('DayOfWeek')[['Cyclists Injured', 'Cyclists Killed']].sum()
logging.debug("\nInjuries by Day of the Week (aggregated):")
logging.debug(injuries_by_day)

# Group by 'Borough' and aggregate injuries and deaths
injuries_by_borough = df_clean.groupby('Borough')[['Cyclists Injured', 'Cyclists Killed']].sum()
logging.debug("\nInjuries by Borough (aggregated):")
logging.debug(injuries_by_borough)

# Group by 'Latitude' and 'Longitude' and aggregate injuries and deaths
injuries_by_location = df_clean.groupby(['Latitude', 'Longitude'])[['Cyclists Injured', 'Cyclists Killed']].sum()
logging.debug("\nInjuries by Location (aggregated):")
logging.debug(injuries_by_location)

# Group by 'Contributing Factor' and aggregate injuries and deaths
factors = df_clean.groupby('Contributing Factor')[['Cyclists Injured', 'Cyclists Killed']].sum()
logging.debug("\nInjuries by Contributing Factor (aggregated):")
logging.debug(factors)

# Get top 5 contributing factors by number of cyclist injuries
top_factors = factors.sort_values(by='Cyclists Injured', ascending=False).head(5)

# Reformat for labeling graph
logging.debug("\nTop 5 Contributing Factors:")
logging.debug(top_factors)

# Create a dictionary for label replacement
label_replacement = {
    'Pedestrian/Bicyclist/Other Pedestrian Error/Confusion': 'Pedestrian Error',
    'Driver Inattention/Distraction': 'Driver Inattention',
    'Failure to Yield Right-of-Way': 'Ignored Right-of-Way',
    'Traffic Control Disregarded' : 'Traffic Control Ignored'
}

# Replace labels in the index of the top_factors DataFrame
top_factors.index = [label_replacement.get(x, x) for x in top_factors.index]

# Plotting all graphs
plt.figure(figsize=(18, 12))

# Injuries by Hour
plt.subplot(2, 2, 1)
sns.barplot(x=injuries_by_hour.index, y=injuries_by_hour['Cyclists Injured'])
plt.title('Cyclist Injuries by Hour')
plt.xlabel('Hour of the Day')
plt.ylabel('Number of Cyclist Injuries')
plt.xticks(rotation=45)

# Injuries by Day of the Week
plt.subplot(2, 2, 2)
sns.barplot(x=injuries_by_day.index, y=injuries_by_day['Cyclists Injured'])
plt.title('Cyclist Injuries by Day of the Week')
plt.xlabel('Day of the Week')
plt.ylabel('Number of Cyclist Injuries')
plt.xticks(rotation=25)

# Injuries by Borough
plt.subplot(2, 2, 3)
sns.barplot(x=injuries_by_borough.index, y=injuries_by_borough['Cyclists Injured'])
plt.title('Cyclist Injuries by Borough')
plt.xlabel('Borough')
plt.ylabel('Number of Cyclist Injuries')
plt.xticks(rotation=25)

# Top 5 Injuries by Contributing Factor
plt.subplot(2, 2, 4)
ax = sns.barplot(x=top_factors.index, y=top_factors['Cyclists Injured'])
plt.title('Cyclist Injuries by Contributing Factor')
plt.xlabel('Contributing Factor')
plt.ylabel('Number of Cyclist Injuries')

# Align x-axis labels with tick marks
ax.set_xticks(range(len(top_factors.index)))
ax.set_xticklabels(top_factors.index, rotation=25, ha='right')

# Adjust layout with padding
plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.22, wspace=0.7, hspace=0.7)  # Add space between plots and margins

# Save the figure
plt.savefig('cyclist_accidents_analysis.png')

# Show the plots
plt.show()
