# -*- coding: utf-8 -*-

"""
main.py

    The main file to run the dash application.
"""

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

# dependencies 
import os
import sys
import dash
import numpy as np
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
# local imports
from src.utils import *
from src.specplot import *
from src.specroutines import get_event_spectra, write_specs
# global paths
import Events


# globals ---------------------------------------------------------------------

# test event
EV = "2012-10-08T12:12:12.760000Z"
# shared specmod spectral group
SP = get_event_spectra(Events.__path__._path[0], EV)

SS = {"stations":{}}

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SPACELAB],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}],
                title="SpecMod Dash"
                )

# app layout ------------------------------------------------------------------

controls = dbc.Card(
    [
        dbc.FormGroup(
            [
                dbc.Label("Select event"),
                dcc.Dropdown(
                    id='event-dropdown',
                    options=[
                        {'label': k[:-4], 
                            'value': k} for k in os.listdir(
                                                        Events.__path__._path[0]
                                                    )
                        ],
                    # value=os.listdir(Events.__path__._path[0])[0],
                    clearable=False,
                    value=os.listdir(Events.__path__._path[0])[0],
                    disabled=True
                ),

            ]
        ),
        dbc.FormGroup(
            [
                dbc.Label("Select station"),
                dcc.Dropdown(
                    id='station-dropdown',
                    options=[
                        {'label': k, 
                            'value': k} for k in SP.get_available_channels()
                        ],
                    value=SP.get_available_channels()[0],
                    clearable=False,
                ),

            ]
        ),
        dbc.FormGroup(
            [
                dbc.Label("Can model?"),
                dcc.RadioItems(
                    id='snr-pass',
                    options=[
                        {'label': 'Yes', 'value': 1},
                        {'label': 'No', 'value': 0},
                        ],
                ),
            ]
        ),
        dbc.FormGroup(
            [
                dbc.Button(
                    'Stage change',
                    id='stage-change',
                    className='mx-2',
                    n_clicks=0,
                ),
            dbc.Tooltip(
                "Click to update changes for spectra.",
                target='stage-change',
                placement="bottom"
                ),
            ]
        ),
        dbc.FormGroup(
            [
            dbc.Button(
                    'Save spectra',
                    id='commit-change',
                    className='mx-2',
                    n_clicks=0,
                ),
            dbc.Tooltip(
                "Click to save changes for spectra back to file.",
                target='commit-change',
                placement="bottom"
                ),
            ]
        ),
    ], body=True
)

app.layout = dbc.Container(
    [
    dcc.Store(id="store"),

    dbc.Row(
        [
            dbc.Col(html.H3("SpecMod Dash"), md=3),
            dbc.Col(
                [
                    html.H1("Spectra Review Panel", 
                        className='text-right text-primary mk-4'), 
                ]
            ),
        ], no_gutters=True
    ),
    html.Hr(),
    dbc.Row(
        [   
            dbc.Col(
                [
                    html.H5("Control Panel", className='text-center'), 
                    html.Hr(), 
                    controls
                ], md=3
            ),

            dbc.Col(
                [   
                    dcc.Graph(
                        id='graph',
                        ),

                    dbc.FormGroup(
                        [
                            dbc.Label("Bandwidth (Hz)"),
                            dcc.RangeSlider(
                                id='slider-position', 
                                min=np.log10(1),
                                max=np.log10(100), 
                                value=np.log10([1, 100]), 
                                step=0.01,
                                marks={i: '{}Hz'.format(
                                        np.round(10 ** i, 1)) for i in np.log10(
                                        [1, 10, 100])},
                                # className="slider",
                                allowCross=False,
                            )
                        ]
                    ),
                ], md=8  
            ), 
        ], align='center'
    ),
    dbc.Row(
        [
        dbc.Col(
            [
            dbc.Alert(
                children=[],
                id="alert-auto",
                dismissable=True,
                is_open=False,
                duration=6000,
            ),
            ], width=12
        ),
        ]
    ),
    ], fluid=True
)

# callbacks -------------------------------------------------------------------

@app.callback(
    Output("store", "data"),
    Input("station-dropdown", "value"),
    State("store", "data")
    )
def update_store(sta, data):

    if sta is None:
        raise dash.exceptions.PreventUpdate

    if data is None or sta not in data["stations"].keys():
        if data is None:
            data = SS
        
        snp = SP.get_spectra(sta)
        # min max frequencies possible
        mn, mx = get_min_max_freqs(snp)
        # min max frequencies of best modeling bandwidth
        mnb, mxb = get_band_vals(snp)
        data["stations"].update(
                    {sta:
                        {
                         "snr": 1 if snp.signal.get_pass_snr() else 0,
                         "min f": mn,
                         "max f": mx,
                         "min bf": mnb,
                         "max bf": mxb,
                         "sf": snp.signal.freq,
                         "sa": snp.signal.amp,
                         "nf": snp.noise.freq,
                         "na": snp.noise.amp,
                        }
                    }
            )
    return data

@app.callback(
    [
        Output('alert-auto', 'children'), 
        Output('alert-auto', 'is_open'),
        Output('store', 'data')
    ],
    [Input('stage-change', 'n_clicks')],
    [
        State('alert-auto', 'is_open'), 
        State('snr-pass', 'value'),
        State('station-dropdown', 'value'),
        State('store', 'data'),
        State('slider-position', 'value')
    ]
)
def stage_change(*args):

    n, is_open, snr, sta, data, bwd = args
    
    if not any_none(args) and n:

        # print(snr, 
        #     data["stations"][sta]["snr"], 
        #     np.power(10, bwd), 
        #     data["stations"][sta]["min bf"], 
        #     data["stations"][sta]["max bf"])
        action = ""

        if snr != data["stations"][sta]["snr"]:

            # if not data["stations"][sta]["snr"]:
            #     data["stations"][sta]["min bf"] = data["stations"][sta]["min f"]
            #     data["stations"][sta]["max bf"] = data["stations"][sta]["max f"]
            
            data["stations"][sta]["snr"] = snr
            
            # print(snr, data["stations"][sta]["snr"])

            yn = {'1':'suitable', '0':'unsuitable'}

            action += f"Marked {sta} as {yn[str(snr)]} for modeling."

        if not np.array_equal(bwd, 
            (data["stations"][sta]["min bf"], 
                data["stations"][sta]["max bf"])
            ):
            data["stations"][sta]["min bf"] = bwd[0]
            data["stations"][sta]["max bf"] = bwd[1]

            if action:
                action += "and "

            action += f"changed bandwidth limits of {sta}."

            
        if action:

            return action, (not is_open), data

        # if bwd

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
    Input("store", "data"),
    State("station-dropdown", "value")
    )   
def display_graph_initial(data, sta):

    # if data is None:
    #     raise dash.exceptions.PreventUpdate
    if any_none(data["stations"], sta):
        return dash.no_update

    tf = data["stations"][sta]["snr"]

    marks = get_marks(
        data["stations"][sta]["min f"], 
        data["stations"][sta]["max f"]
        )

    fig = make_fig(
        np.array(data["stations"][sta]["sf"]), 
        np.array(data["stations"][sta]["sa"]),
        np.array(data["stations"][sta]["nf"]), 
        np.array(data["stations"][sta]["na"]),
        tf,
        (data["stations"][sta]["min bf"], 
         data["stations"][sta]["max bf"]),
        )

    return (
        fig, 
        (data["stations"][sta]["min bf"], data["stations"][sta]["max bf"]),
        not tf, # turns off the range slider if it can't be modeled
        data["stations"][sta]["min f"], 
        data["stations"][sta]["max f"], 
        marks, 
        tf
        )


@app.callback(
    Output("graph", "figure"),
    Input("slider-position", "value"),
    [State("graph", "figure"),
     State("store", "data"),
     State("station-dropdown", "value")   
    ])
def display_graph_update(npos, fig, data, sta):

    if not any_none(npos, fig, data, sta):

        fig = go.Figure(fig)

        if data["stations"][sta]["snr"]:
           
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

    return dash.no_update

@app.callback(
    [
     Output('alert-auto', 'children'), 
     Output('alert-auto', 'is_open'),
    ],
    [Input('commit-change', "n_clicks")],
    [
     State("alert-auto", "is_open"),
     State("event-dropdown", "value"),
     State("store", "data")
    ]
    )
def commit_updates_and_save(*args):

    n, is_open, ev, data = args

    if not any_none(n, is_open, ev, data):

        if n and data["stations"] is not None:
            
            print(args[:-1])

            write_specs(Events.__path__._path[0], ev, data)

            msg = f"Saved spectra for {ev} for {[sta for sta in data['stations'].keys()]}."
            
            if is_open:
                is_open = False

            return msg, (not is_open)
    
    return dash.no_update

if __name__ == '__main__':
    app.run_server(debug=True)