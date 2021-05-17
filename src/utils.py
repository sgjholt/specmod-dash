"""
A module that contains utility functions for specmod-dash.
"""

import plotly.graph_objects as go


def trace_in_fig(fig: go.Figure, name: str) -> bool:
	"""
	Looks for the trace with a given name and returns True if
	it exists or False if it does not.

	Args:
		fig (plotly.graph_ojects.Figure): A figure object to be checked.
		name (str): The name of the trace to look for.

	Returns:
		tr (bool): True if the trace is in figure, False otherwise.
	"""

	tf = False
	for trace in fig['data']:
		try:
			if trace['name'] in [name]:
				return not tf 
		except TypeError:
			continue
	return tf

def is_auto_bandwidth(fig, pos):

	for trace in fig['data']:
		if 10**pos == trace['x'][0]:
				return True

	return False 

def any_none(*args):
    return [x for x in args if x is None]