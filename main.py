# -*- coding: utf-8 -*-

"""
main.py

	The main file to run the dash application.
"""

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.


import dash
import numpy as np
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

from specplot import *
from loadspec import get_event_spectra, ev
from dash.dependencies import Input, Output








# globals ---------------------------------------------------------------------
SP = get_event_spectra(ev)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SPACELAB],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}],
                title="SpecMod"
                )

# app layout ------------------------------------------------------------------
app.layout = dbc.Container([

	dbc.Row([
		dbc.Col(
			html.H1("Spectra Review Panel", 
				className='text-center text-primary mb-4'), width=12
			)
		]),

	dbc.Row([
		dbc.Col([

				html.H5("Select Station", className='text-center'),

			    dcc.Dropdown(
			        id='station-dropdown',
			        options=[{'label': k, 'value': k} for k in SP.get_available_channels()],
			        value=SP.get_available_channels()[0],
			        clearable=False
			        ),
			        # style=dict(width="50%"),

			], width=4),
		dbc.Col([

			html.H5("Suitable for modeling?"),

			dcc.RadioItems(
				id='snr-pass',
    			options=[
        			{'label': 'True', 'value': 1},
        			{'label': 'False', 'value': 0},
    			],
    			value=1
    			)
			])
		]),

	dbc.Row(
		dbc.Col([	

		    dcc.Graph(
		        id='graph',
		        ),
	
   			html.H5(
   				"Bandwidth (Hz)", 
   				className="text-center"
   				),

	        dcc.RangeSlider(
		        id='slider-position', 
		        min=np.log10(0.01),
		        max=np.log10(100), 
		        value=np.log10([1, 10]), 
		        step=0.01,
		        marks={i: '{}'.format(
		        		np.round(10 ** i, 1)) for i in np.log10(
		        		[0.1, 1, 10, 20, 50])},
		       	# className="slider",
		       	allowCross=False,
			    ),
	        ]),  
    	),
	dbc.Row(
		dbc.Col(
			html.Pre(id='log'),
			)
		)
    ])


# callbacks 

@app.callback(
    Output('log', 'children'),
    Input('slider-position', 'value'))
def display_selected_data(vals):
    return f'min f: {10**vals[0]:.1f}, max f: {10**vals[1]:.1f}' 

@app.callback([
	 Output("graph", "figure"), 
     Output("slider-position", "value"),
     Output("slider-position", "min"),
     Output("slider-position", "max"),
     Output("slider-position", "marks"),
     Output("snr-pass", "value")
    ],
    [Input("station-dropdown", "value"), ]
    )
def display_graph_initial(station):

	global SP

	snp = SP.get_spectra(station)

	mn, mx = get_min_max_freqs(snp)

	marks = get_marks(mn, mx)

	value = get_band_vals(snp)

	fig = make_fig(
		snp.signal.freq, 
		snp.signal.amp,
		snp.noise.freq, 
		snp.noise.amp,
		value,
		)

	return fig, value, mn, mx, marks, 1 if snp.signal.get_pass_snr() else 0


@app.callback(
     Output("graph", "figure"),
     [Input("slider-position", "value"),
      Input("station-dropdown", "value"),
      Input("snr-pass", "value")]
     )
def display_graph_update(pos, station, snr):

	global SP

	snp = SP.get_spectra(station)
	snp.signal.set_pass_snr(snr)

	value = get_band_vals(snp)

	fig = make_fig(
		snp.signal.freq, 
		snp.signal.amp,
		snp.noise.freq, 
		snp.noise.amp,
		value,
		pos,
		)

	return fig





if __name__ == '__main__':
    app.run_server(debug=True)