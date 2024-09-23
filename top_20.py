import mysql.connector
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
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

# Updated SQL query to exclude rows with NULL scores
query = """
SELECT jokeid, date, venue, score
FROM jokes
WHERE score IS NOT NULL;
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
joke_sets = {}
for row in results:
    jokeid, date, venue, score = row
    key = (date, venue)
    if key not in joke_sets:
        joke_sets[key] = []
    joke_sets[key].append((jokeid, score))

logging.info(f"Processed {len(joke_sets)} unique joke sets (venue + date).")

# Fuzzy matching to group similar jokeids
def combine_similar_jokeids(jokeids, similarity_threshold=80):
    grouped_jokeids = {}
    for jokeid in jokeids:
        match = process.extractOne(jokeid, grouped_jokeids.keys(), scorer=fuzz.ratio)
        logging.debug(f"Processing jokeid: {jokeid}")
        
        if match is not None:
            best_match, score = match[0], match[1]
            logging.debug(f"Best match for {jokeid}: {best_match} with score {score}")
            if score >= similarity_threshold:
                grouped_jokeids[best_match].append(jokeid)
                logging.debug(f"Grouped {jokeid} with {best_match}")
            else:
                grouped_jokeids[jokeid] = [jokeid]
                logging.debug(f"Created new group for {jokeid}")
        else:
            grouped_jokeids[jokeid] = [jokeid]
            logging.debug(f"No match found for {jokeid}, created new group.")
    return grouped_jokeids

# Combine jokeids based on similarity
jokeids = [row[0] for row in results]
logging.info("Combining similar jokeids based on fuzzy matching...")
similar_jokeid_groups = combine_similar_jokeids(jokeids)
logging.info(f"Found {len(similar_jokeid_groups)} unique jokeid groups.")

# Calculate average scores for similar jokeid groups
average_scores = {}
for group, similar_jokes in similar_jokeid_groups.items():
    total_score = sum(score for jokeid in similar_jokes for jokeid_data in results if jokeid == jokeid_data[0] for score in [jokeid_data[3]])
    avg_score = total_score / len(similar_jokes)
    average_scores[group] = avg_score

logging.info(f"Calculated average scores for {len(average_scores)} groups.")

# Extract the top 20 jokeid groups based on average score for heatmap analysis
top_jokeids = [jokeid for jokeid, _ in sorted(average_scores.items(), key=lambda item: item[1], reverse=True)[:20]]

# Create a mapping from jokeid to index
jokeid_to_index = {jokeid: idx for idx, jokeid in enumerate(top_jokeids)}

# Create a score matrix for the top 20 jokeids
score_matrix = np.zeros((len(top_jokeids), len(top_jokeids)))

# Populate the score matrix based on co-occurrence in the same sets (venue + date)
for joke_set in joke_sets.values():
    for i, (jokeid1, score1) in enumerate(joke_set):
        if jokeid1 in top_jokeids:
            for jokeid2, score2 in joke_set[i+1:]:
                if jokeid2 in top_jokeids:
                    idx1, idx2 = jokeid_to_index[jokeid1], jokeid_to_index[jokeid2]
                    if (idx1 == idx2):
                        avg_score = 0
                    else:
                        avg_score = (score1 + score2) / 2  # Average score for co-occurrence
                    score_matrix[idx1, idx2] = avg_score
                    score_matrix[idx2, idx1] = avg_score  # Symmetric matrix

# Plot the heatmap with larger figure size and improved readability
plt.figure(figsize=(12, 10))
sns.heatmap(score_matrix, annot=True, fmt=".1f", cmap="YlGnBu",
            xticklabels=top_jokeids, yticklabels=top_jokeids, linewidths=.5)

plt.title("Heatmap of Joke Scores for Top 20 JokeIDs")
plt.xlabel("JokeID")
plt.ylabel("JokeID")
plt.xticks(rotation=45, ha='right')  # Rotate x-axis labels for better readability
plt.tight_layout()

# Save the plot to a file
plt.savefig('jokes_heatmap_analysis_fixed.png')
logging.info("Heatmap saved as 'jokes_heatmap_analysis_fixed.png'.")

# Show the plot
logging.info("Displaying the heatmap for top jokeid groups...")
plt.show()
