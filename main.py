# -*- coding: utf-8 -*-

"""
main.py

    The main file to run the dash application.
"""

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import os
import dash
import numpy as np
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

from src.specplot import *
from src.loadspec import get_event_spectra, ev
from src.utils import *
from dash.dependencies import Input, Output, State

import Events
# globals ---------------------------------------------------------------------
SP = get_event_spectra(Events.__path__._path[0], ev)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SPACELAB],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}],
                title="SpecMod Dash"
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
        dbc.Col([
            html.Hr(),
                html.Details([
                    html.Summary('Contents of figure storage'),
                        dcc.Markdown(
                            id='log'
                        )
                    ])
            ])
        )
    ])


# callbacks 

@app.callback(
    Output('log', 'children'),
    Input('slider-position', 'value')
    )
def display_selected_data(vals):
    x = None
    if vals is not None:
        x = f'min f: {10**vals[0]:.1f}, max f: {10**vals[1]:.1f}'
    return x

@app.callback([
     Output("graph", "figure"), 
     Output("slider-position", "value"),
     Output("slider-position", "min"),
     Output("slider-position", "max"),
     Output("slider-position", "marks"),
     Output("snr-pass", "value"),
    ],
     Input("station-dropdown", "value")
    )
def display_graph_initial(station):

    snp = SP.get_spectra(station)

    mn, mx = get_min_max_freqs(snp)

    marks = get_marks(mn, mx)

    value = get_band_vals(snp)

    fig = make_fig(
        snp.signal.freq, 
        snp.signal.amp,
        snp.noise.freq, 
        snp.noise.amp,
        snp.signal.get_pass_snr(),
        value,
        )

    return fig, value, mn, mx, marks, (1 if snp.signal.get_pass_snr() else 0)


@app.callback(
    Output("graph", "figure"),
    Input("slider-position", "value"),
    State("graph", "figure"),
    )
def display_graph_update(npos, fig):


    fig = go.Figure(fig)

    if not check_for_none(npos, fig, fig['layout']['yaxis']['range']):

        for pos, nm in zip(npos, ['start', 'end']):
            
            name = f"new bandwidth {nm}"

            if not is_auto_bandwidth(fig, pos):
                if not trace_in_fig(fig, name):
                    fig.add_trace(
                        go.Scatter(
                            x=[10**pos, 10**pos], 
                            y=np.power(10, fig['layout']['yaxis']['range']),
                            mode='lines',
                            line_width=3,
                            line_dash='dash',
                            line_color='green', 
                            name=f"new bandwidth {nm}", 
                        )
                    )

                else:
                    fig.for_each_trace(
                        lambda trace: trace.update(
                            x=[10**pos, 10**pos],

                            ) if trace.name == name else (),
                        )

    return fig

@app.callback(
    [Output("log", "children"), ],
    [Input("snr-pass", "value"), ],
    [State("station-dropdown", "value"), ],
    )
def change_snr(snr, sta):

    if sta is not None:
        snp = SP.get_spectra(sta)
        if snr is not None:
            print(snr)
            print(f"{sta} pass snr is {snp.signal.get_pass_snr()}")
            if bool(snr) != snp.signal.get_pass_snr():
                snp.signal.set_pass_snr(bool(snr))
                return(f"changed {sta} pass snr to {bool(snr)}", )
        return [f"{sta} has snr {bool(1 if snp.signal.get_pass_snr() else 0)}", ]
    raise dash.exceptions.PreventUpdate





    


if __name__ == '__main__':
    app.run_server(debug=True)