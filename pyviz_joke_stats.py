import mysql.connector
import pandas as pd
import networkx as nx
import pyvista as pv
import numpy as np
from fuzzywuzzy import fuzz, process
import argparse

def fuzzy_group_jokes(df, threshold=70):
    """
    Group similar joke IDs using fuzzy string matching.
    Jokes with a similarity score greater than or equal to the threshold will be grouped.
    The shortest joke ID in each group will be used as the canonical group ID.
    """
    jokeid_list = df['current_jokeid'].unique()
    jokeid_to_group = {}

    # Iterate through all jokeids and group them by similarity
    for jokeid in jokeid_list:
        # Check if the jokeid is already grouped
        if jokeid not in jokeid_to_group:
            # Find all similar jokeids based on the threshold
            similar_jokes = process.extractBests(jokeid, jokeid_list, scorer=fuzz.token_sort_ratio, score_cutoff=threshold)
            group = [joke[0] for joke in similar_jokes]
            
            # Find the shortest joke ID in the group to use as the canonical group ID
            shortest_jokeid = min(group, key=len)

            # Map all jokes in the group to the shortest joke ID
            for similar_joke in group:
                jokeid_to_group[similar_joke] = shortest_jokeid

    # Replace both current and preceding joke IDs with the group ID
    df['current_jokeid'] = df['current_jokeid'].map(jokeid_to_group)
    df['preceding_jokeid'] = df['preceding_jokeid'].map(jokeid_to_group)

    return df

def analyze_jokes(df):
    # Drop rows where the preceding_jokeid is null (first jokes in sets)
    df = df.dropna(subset=['preceding_jokeid'])

    # Ensure there are no NaN values in current_score before grouping
    df = df.dropna(subset=['current_score'])

    # Group by current jokeid and preceding jokeid, calculate average score and count
    grouped = df.groupby(['current_jokeid', 'preceding_jokeid']).agg(
        avg_score=('current_score', 'mean'),
        count=('current_score', 'size')
    ).reset_index()

    # Ensure there are no NaN values in avg_score before selecting the best joke
    grouped = grouped.dropna(subset=['avg_score'])
    grouped.to_csv("grouped_filter_no_sort.csv")

    # Find the best preceding joke for each current joke (highest average score)
    best_preceding_jokes = grouped.loc[grouped.groupby('current_jokeid')['avg_score'].idxmax()]

    # Sort by count in descending order
    best_preceding_jokes = best_preceding_jokes.sort_values(by='count', ascending=False)

    # Display the sorted results
    print("Best preceding jokes for each jokeid (sorted by count):")
    print(best_preceding_jokes)

    # Optional: Save results to a CSV file
    best_preceding_jokes.to_csv('best_preceding_jokes_sorted_by_count.csv', index=False)

    return best_preceding_jokes

def plot_top_joke_network(best_preceding_jokes):
    """
    Plot a 3D network graph showing the top scoring jokes and their good preceding jokes, with directional arrows.
    """
    # Select the top 20 scoring jokes
    top_jokes = best_preceding_jokes.nlargest(20, 'count')

    # Create a directed graph
    G = nx.DiGraph()

    # Add edges between top jokes and their preceding jokes
    for _, row in top_jokes.iterrows():
        print("adding edge btwn :: "+str(row['preceding_jokeid']+"->"+str(row['current_jokeid'])))
        G.add_edge(row['preceding_jokeid'], row['current_jokeid'])

    # Use spring layout to position nodes in 3D
    pos = nx.spring_layout(G, dim=3, k=0.7, iterations=100)

    # Extract node positions as a list of coordinates
    node_positions = np.array([pos[node] for node in G.nodes()])

    # Create a PyVista plotter
    plotter = pv.Plotter()

    # Add nodes as spheres
    for i, node in enumerate(G.nodes()):
        plotter.add_mesh(pv.Sphere(center=(node_positions[i][0], node_positions[i][1], node_positions[i][2]), radius=0.05), color='skyblue')

    # Create edges and add them to the plotter with arrows
    for edge in G.edges():
        start = np.array(pos[edge[0]])
        end = np.array(pos[edge[1]])

        # Add line for the edge
        plotter.add_lines(np.array([start, end]), color='blue', width=2)

        # Compute the direction and length of the edge
        direction = end - start
        length = np.linalg.norm(direction)

        # Normalize the direction vector
        direction = direction / length

        # Scale the arrow based on the edge length (adjusting scale factor as needed)
        arrow = pv.Arrow(start, direction, scale=length * 0.9, shaft_radius=0.01, tip_radius=0.05)

        plotter.add_mesh(arrow, color='red')

    # Offset the labels slightly from the nodes for better visibility
    offset = 0.1  # Adjust this value to move labels further away from the nodes
    label_positions = node_positions + offset
    
    # Use add_point_labels to add labels to nodes
    labels = list(G.nodes())
    plotter.add_point_labels(label_positions, labels, point_size=5, font_size=12, text_color="black", shape=None)

    # Show the plot
    plotter.show()

def main():
    # Argument parser for command-line arguments
    parser = argparse.ArgumentParser(description="Analyze jokes and plot joke networks.")
    parser.add_argument('--password', required=True, help='Password for MySQL database')

    args = parser.parse_args()

    # Connect to MySQL database using provided password
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password=args.password,
        database="jokes"
    )

    # Run the updated SQL query to get the data
    query = """
    SELECT j1.jokeid AS current_jokeid, j1.score AS current_score, j2.jokeid AS preceding_jokeid
    FROM jokes j1
    LEFT JOIN jokes j2
    ON j1.date = j2.date AND j1.venue = j2.venue AND j1.id = j2.id + 1
    WHERE j1.jokeid IN (
        SELECT jokeid
        FROM jokes
        GROUP BY jokeid
        HAVING COUNT(*) >= 10
    )
    AND j2.jokeid IN (
        SELECT jokeid
        FROM jokes
        GROUP BY jokeid
        HAVING COUNT(*) >= 10
    )
    AND j1.score IS NOT NULL;
    """
    df = pd.read_sql(query, conn)

    # Apply fuzzy grouping
    df = fuzzy_group_jokes(df)

    # Analyze the jokes and get the best preceding jokes
    best_preceding_jokes = analyze_jokes(df)

    # Plot the network graph of top scoring jokes and their preceding jokes
    plot_top_joke_network(best_preceding_jokes)

    # Close the database connection
    conn.close()

if __name__ == "__main__":
    main()
