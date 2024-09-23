import mysql.connector
import matplotlib.pyplot as plt
from collections import Counter
from rapidfuzz import fuzz, process
import logging

# Set up logging to write to a file
logging.basicConfig(filename='jokes_analysis.log',
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Connect to the MySQL database
logging.info("Connecting to the database...")
connection = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='jokes'
)

cursor = connection.cursor()

# Query to get sets that contain "AI_killing_poetry" with a high score
query = """
SELECT t1.jokeid, t1.date, t1.venue, t1.score
FROM jokes AS t1
JOIN (
    SELECT date, venue
    FROM jokes
    WHERE jokeid = 'AI_killing_poetry' AND score > (SELECT AVG(score) FROM jokes WHERE jokeid = 'AI_killing_poetry')
) AS AI_killing_poetry_sets
ON t1.date = AI_killing_poetry_sets.date AND t1.venue = AI_killing_poetry_sets.venue
WHERE t1.jokeid != 'AI_killing_poetry'
ORDER BY t1.date, t1.venue, t1.score DESC;
"""

logging.info("Executing SQL query to retrieve jokes data...")
cursor.execute(query)

# Store the results
results = cursor.fetchall()
logging.info(f"Retrieved {len(results)} rows from the database.")

# Close the database connection
cursor.close()
connection.close()
logging.info("Database connection closed.")

# Process the results to find frequently occurring jokeids
jokeids = [row[0] for row in results]
logging.info(f"Processing {len(jokeids)} jokeids.")

# Fuzzy matching to group similar jokeids
def combine_similar_jokeids(jokeids, similarity_threshold=80):
    grouped_jokeids = {}
    
    for jokeid in jokeids:
        # Try to find a jokeid that is already in the group with high similarity
        match = process.extractOne(jokeid, grouped_jokeids.keys(), scorer=fuzz.ratio)
        
        # Log each jokeid being processed
        logging.debug(f"Processing jokeid: {jokeid}")
        
        # Check if a match was found and if the similarity score meets the threshold
        if match is not None:
            best_match, score = match[0], match[1]
            logging.debug(f"Best match for {jokeid}: {best_match} with score {score}")
            if score >= similarity_threshold:
                # Combine this jokeid with an existing one
                grouped_jokeids[best_match].append(jokeid)
                logging.debug(f"Grouped {jokeid} with {best_match}")
            else:
                # Create a new group for this jokeid
                grouped_jokeids[jokeid] = [jokeid]
                logging.debug(f"Created new group for {jokeid}")
        else:
            # No match found, create a new group for this jokeid
            grouped_jokeids[jokeid] = [jokeid]
            logging.debug(f"No match found for {jokeid}, created new group.")

    return grouped_jokeids

# Combine jokeids based on similarity
logging.info("Combining similar jokeids based on fuzzy matching...")
similar_jokeid_groups = combine_similar_jokeids(jokeids)
logging.info(f"Found {len(similar_jokeid_groups)} unique jokeid groups.")

# Combine frequencies for similar jokeid groups
grouped_frequencies = Counter()
for group, similar_jokes in similar_jokeid_groups.items():
    # Count the total frequency of all jokes in the group
    count = sum(jokeids.count(joke) for joke in similar_jokes)
    grouped_frequencies[group] = count

logging.info(f"Generated frequency data for {len(grouped_frequencies)} groups.")

# Extract the top 20 jokeid groups and their counts for visualization
top_jokeids = [jokeid for jokeid, count in grouped_frequencies.most_common(30)]
top_counts = [count for jokeid, count in grouped_frequencies.most_common(30)]

# Create a bar chart for the top 20 most frequent jokeid groups
plt.figure(figsize=(10, 6))
plt.barh(top_jokeids, top_counts, color='skyblue')
plt.xlabel('Frequency')
plt.ylabel('JokeID Group')
plt.title('Most Frequent JokeID Groups in High Scoring Sets with "AI_killing_poetry"')
plt.gca().invert_yaxis()  # Invert y-axis to show the most frequent at the top
plt.tight_layout()

# Save the plot to a file
plt.savefig('jokes_analysis_plot.png')
logging.info("Bar chart saved as 'jokes_analysis_plot.png'.")

# Show the plot
logging.info("Displaying the bar chart for top jokeid groups...")
plt.show()
