# -*- coding: utf-8 -*-

"""
main.py

    The main file to run the dash application.
"""

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

# dependencies 
import os
import dash
import numpy as np
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
# local imports
from src.utils import *
from src.specplot import *
from src.specroutines import get_event_spectra
# global paths
import Events


# globals ---------------------------------------------------------------------

# test event
EV = "2012-10-08T12:12:12.760000Z"
# shared specmod spectral group
SP = get_event_spectra(Events.__path__._path[0], EV)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SPACELAB],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}],
                title="SpecMod Dash"
                )

# app layout ------------------------------------------------------------------
app.layout = dbc.Container([

    dcc.Store(id="store"),

    dbc.Row([
        dbc.Col([
            dbc.Alert(
                children=[],
                id="alert-auto",
                dismissable=True,
                is_open=False,
                duration=8000
            ),
            ], width=12),
        ]),

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
                    {'label': 'Yes', 'value': 1},
                    {'label': 'No', 'value': 0},
                ],
                )
            ]),
        dbc.Col([

            html.H5('Control Panel'),

            dbc.Button(
                'stage change',
                id='stage-change',
                className='mr-2',
                n_clicks=0,
                )
            ]),
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
    ])


# callbacks 

@app.callback(
    Output("store", "data"),
    Input("station-dropdown", "value"),
    )
def update_store(sta):

    snp = SP.get_spectra(sta)
    # min max frequencies possible
    mn, mx = get_min_max_freqs(snp)
    # min max frequencies of best modeling bandwidth
    mnb, mxb = get_band_vals(snp)
        
    return {"station":sta, 
            "snr": 1 if snp.signal.get_pass_snr() else 0,
            "min f": mn,
            "max f": mx,
            "min bf":mnb,
            "max bf":mxb,
            }

@app.callback(
    [Output('alert-auto', 'children'), 
     Output('alert-auto', 'is_open'),
     Output('station-dropdown', 'value'),
     ],
    [Input('stage-change', 'n_clicks')],
    [State('alert-auto', 'is_open'), 
     State('snr-pass', 'value'),
     State('store', 'data')]
)
def stage_change(*args):

    n, is_open, snr, data = args
    
    if not any_none(args) and n:

        snp = SP.get_spectra(data["station"])

        print(snr, data["snr"])
        
        if snr != data["snr"]:
            
            snp.signal.set_pass_snr(bool(snr))

            yn = {'1':'suitable', '0':'unsuitable'}

            action = f"Marked {data['station']} as {yn[str(snr)]} for modeling."

            print(snr, data["snr"])
            return action, (not is_open), data["station"]


    raise dash.exceptions.PreventUpdate


@app.callback([
     Output("graph", "figure"), 
     Output("slider-position", "value"),
     Output("slider-position", "disabled"),
     Output("slider-position", "min"),
     Output("slider-position", "max"),
     Output("slider-position", "marks"),
     Output("snr-pass", "value"),
    ],
    # Input("station-dropdown", "value")
    Input("store", "data")
    )   
def display_graph_initial(data):

    # if data is None:
    #     raise dash.exceptions.PreventUpdate

    sta = data['station']

    snp = SP.get_spectra(sta)

    tf = data["snr"]

    marks = get_marks(data["min f"], data["max f"])

    # value = get_band_vals(snp)

    fig = make_fig(
        snp.signal.freq, 
        snp.signal.amp,
        snp.noise.freq, 
        snp.noise.amp,
        tf,
        (data["min bf"], data["max bf"]),
        )

    return (
        fig, 
        (data["min bf"], data["max bf"]),
        not tf, # turns off the range slider if it can't be modeled
        data["min f"], 
        data["max f"], 
        marks, 
        tf
        )


@app.callback(
    Output("graph", "figure"),
    Input("slider-position", "value"),
    [State("graph", "figure"),
     State("snr-pass", "value")   
    ])
def display_graph_update(npos, fig, snr):


    if not snr:
        raise dash.exceptions.PreventUpdate

    fig = go.Figure(fig)

    if not any_none(npos[0], fig, fig['layout']['yaxis']['range']):

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



if __name__ == '__main__':
    app.run_server(debug=True)