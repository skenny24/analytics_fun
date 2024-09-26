# analytics_fun
## sandbox for playing with various datasets

### joke pairing data

view best joke to precede another
```python
> pyviz_joke_stats.py`
```
![Watch the video](vista.gif)
show heatmap of average score for pairings of the top 20 (highest scoring) jokes  
```python
> python top_20.py 
```
<div style="display: flex; justify-content: space-between;">
  <img src="jokes_heatmap_analysis_fixed.png" alt="more joke database analysis" style="width: 50%;"/>
</div>

call with a specific joke to determine best set options
```python
> python joke_stats.py AI_killing_poetry
```
<div style="display: flex; justify-content: space-between;">
  <img src="jokes_analysis_plot.png" alt="joke database analysis" style="width: 50%;"/>
</div>



### cycling data assessing when and where cyclists are most likely to get injured

<div style="display: flex; justify-content: space-between;">
  <img src="cyclist_accidents_analysis.png" alt="cycling" style="width: 100%;"/>
</div>
