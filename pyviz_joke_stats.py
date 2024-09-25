import mysql.connector
import pandas as pd
import networkx as nx
import pyvista as pv
import numpy as np

def fuzzy_group_jokes(df):
    # Dummy implementation for fuzzy grouping
    # Replace this with your actual fuzzy grouping logic
    df['grouped_jokeid'] = df['current_jokeid']  # Just a placeholder
    df['avg_score'] = df['current_score']  # Just a placeholder
    return df

def analyze_jokes(df):
    # Dummy implementation for analyzing jokes
    # Replace this with your actual analysis logic
    return df[['grouped_jokeid', 'preceding_jokeid', 'avg_score']]

def plot_top_joke_network(best_preceding_jokes):
    """
    Plot a 3D network graph showing the top scoring jokes and their good preceding jokes.
    """
    # Select the top 20 scoring jokes
    top_jokes = best_preceding_jokes.nlargest(20, 'avg_score')

    # Create a directed graph
    G = nx.DiGraph()

    # Add edges between top jokes and their preceding jokes
    for _, row in top_jokes.iterrows():
        G.add_edge(row['grouped_jokeid'], row['preceding_jokeid'], weight=row['avg_score'])

    # Use spring layout to position nodes in 3D
    pos = nx.spring_layout(G, dim=3, k=0.5, iterations=100)

    # Extract node positions as a list of coordinates
    node_positions = np.array([pos[node] for node in G.nodes()])

    # Create a PyVista plotter
    plotter = pv.Plotter()

    # Add nodes as spheres
    for i, node in enumerate(G.nodes()):
        plotter.add_mesh(pv.Sphere(center=(node_positions[i][0], node_positions[i][1], node_positions[i][2]), radius=0.1), color='skyblue')

    # Create edges and add them to the plotter
    edges = []
    for edge in G.edges():
        start = pos[edge[0]]
        end = pos[edge[1]]
        edges.append(start)
        edges.append(end)

    # Convert edges to a PyVista format
    edges = np.array(edges).reshape(-1, 3)  # Reshape to pairs of points
    plotter.add_lines(edges, color='blue', width=2)

    # Use add_point_labels to add labels to nodes
    labels = list(G.nodes())
    plotter.add_point_labels(node_positions, labels, point_size=0.1, font_size=12, text_color="black", shape=None)

    # Set plot title
    plotter.add_title("Top 20 Scoring Jokes and Their Preceding Jokes")

    # Show the plot
    plotter.show()

def main():
    # Connect to MySQL database
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
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
        HAVING COUNT(*) >= 5
    )
    AND j2.jokeid IN (
        SELECT jokeid
        FROM jokes
        GROUP BY jokeid
        HAVING COUNT(*) >= 5
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
