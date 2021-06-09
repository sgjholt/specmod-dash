"""
A module that contains utility functions for specmod-dash.
"""

import yaml 
import plotly.graph_objects as go


def get_config(name: str = "config.yaml") -> dict:
    """
    Parses an arbitrary config file. Assumes the default will be 
    'config.yaml'.

    Args:
        name (str): The name of the YAML file. Default is "config.yaml".

    Returns:
        opt (dict): A dictionary containing the parsed YAML file.
    """
    with open(f"{name}", 'r') as config:
        opts = yaml.safe_load(config)
    return opts

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

def is_auto_bandwidth(fig: go.Figure, pos: float) -> bool:
    """
    Looks at the figure object and tries to find an x value with exactly
    the same value as pos. This would be the automatic bandwidth value.
    
    Args:
        fig (plotly.graph_ojects.Figure): A figure object to be checked.
        name (str): The name of the trace to look for.

    Returns:
        True if the trace is in figure, False otherwise.        
    """

    for trace in fig['data']:
        if 10**pos == trace['x'][0]:
                return True

    return False 

def any_none(*args) -> bool:
    """
    bool
        True if any of the arguments is type None.
    """
    return [x for x in args if x is None]