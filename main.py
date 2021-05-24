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

SS = {}

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SPACELAB],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}],
                title="SpecMod Dash"
                )

# app layout ------------------------------------------------------------------

controls = dbc.Card(
    [
        dbc.CardHeader(html.H5("Control Panel", className='text-center')),
        dbc.CardBody(
        [
            dbc.FormGroup(
                [
                    dbc.Label("Select event"),
                    dcc.Dropdown(
                        id='event-dropdown',
                        options=[
                            {
                                'label': k[:-4], 
                                'value': k
                            } for k in sorted(
                                os.listdir(Events.__path__._path[0]))
                                ],
                        value=sorted(os.listdir(Events.__path__._path[0]))[0],
                        clearable=False,
                        # disabled=True
                    ),

                    dbc.Label("Select station"),
                    dcc.Dropdown(
                        id='station-dropdown',
                        clearable=False,
                    ),

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
            dbc.Label("Commit changes"),
            dbc.ButtonGroup(
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
            ],
        )
    ], color="dark", outline=True, 
)

infocard = dbc.Card(
    [
        dbc.CardHeader(html.H5("Metadata", className='text-left')),
        dbc.CardBody(
            [
                dbc.ListGroup(
                    [
                        dbc.ListGroupItem(
                            [
                                dbc.ListGroupItemHeading("Hypo. Dist (km)"),
                                dbc.ListGroupItemText("", id='hypo-dist'),
                            ]
                        ),
                        dbc.ListGroupItem(                            [
                                dbc.ListGroupItemHeading("Epi. Dist (km)"),
                                dbc.ListGroupItemText("", id='epi-dist'),
                            ],
                        ),
                    ], horizontal=True,
                ),
            ]
        )
    ]
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
                dbc.Col(controls, md=3),

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
                                    className="slider",
                                    allowCross=False,
                                )
                            ]
                        ),
                        html.Hr(),
                    ], md=8  
                ), 
            ], align='center'
        ),
        dbc.Row(
            [
                dbc.Col([infocard, ]),
                
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
            ], align='center'
        ),
    ], fluid=True, style={'font-family' : '"Times New Roman"'},
)

# callbacks -------------------------------------------------------------------


@app.callback(
    [
     Output("station-dropdown", "value"),
     Output("station-dropdown", "options"),
    ],
    Input("event-dropdown", "value")
    )
def update_station_dropdown(ev):

    sp = get_event_spectra(Events.__path__._path[0], ev)

    value = sorted(sp.group.values(), 
        key=lambda x: x.signal.meta['rhyp'])[0].id

    options = [
                {
                 'label': k.id, 
                 'value': k.id,
                } for k in sorted(sp.group.values(), 
                    key=lambda x: x.signal.meta['rhyp'])
            ]

    return value, options



@app.callback(
    Output("store", "data"),
    Input("station-dropdown", "value"),
    [
     State("event-dropdown", "value"),
     State("store", "data"),
    ]
)
def update_store(sta, ev, data):

    if any_none(sta, ev):
        raise dash.exceptions.PreventUpdate

    if data is None:
        data = SS

    if ev not in data.keys():
        data[ev] = {}

    if sta not in data[ev].keys():
        
        sp = get_event_spectra(Events.__path__._path[0], ev)

        snp = sp.get_spectra(sta)
        # min max frequencies possible
        mn, mx = get_min_max_freqs(snp)
        # min max frequencies of best modeling bandwidth
        mnb, mxb = get_band_vals(snp)
        

        metdat = {
                    sta:
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
                         "meta": snp.signal.meta
                        }
                    }

        data[str(ev)].update(metdat)

    return data

@app.callback(
    [
        Output('alert-auto', 'children'), 
        Output('alert-auto', 'is_open'),
        Output('store', 'data'),
    ],
    [Input('stage-change', 'n_clicks')],
    [
        State('alert-auto', 'is_open'), 
        State('snr-pass', 'value'),
        State('station-dropdown', 'value'),
        State('store', 'data'),
        State('slider-position', 'value'),
        State('event-dropdown', 'value'),
    ]
)
def stage_change(*args):

    n, is_open, snr, sta, data, bwd, ev = args
    
    if not any_none(args) and n:

        # print(snr, 
        #     data["stations"][sta]["snr"], 
        #     np.power(10, bwd), 
        #     data["stations"][sta]["min bf"], 
        #     data["stations"][sta]["max bf"])
        action = ""

        if snr != data[ev][sta]["snr"]:

            # if not data["stations"][sta]["snr"]:
            #     data["stations"][sta]["min bf"] = data["stations"][sta]["min f"]
            #     data["stations"][sta]["max bf"] = data["stations"][sta]["max f"]
            
            data[ev][sta]["snr"] = snr
            
            # print(snr, data["stations"][sta]["snr"])

            yn = {'1':'suitable', '0':'unsuitable'}

            action += f"Marked {sta} as {yn[str(snr)]} for modeling."

        if not np.array_equal(bwd, 
            (data[ev][sta]["min bf"], 
                data[ev][sta]["max bf"])
            ):
            data[ev][sta]["min bf"] = bwd[0]
            data[ev][sta]["max bf"] = bwd[1]

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
     Output('epi-dist', 'children'), 
     Output('hypo-dist', 'children'),
    ],
    # Input("station-dropdown", "value")
    Input("store", "data"),
    State("station-dropdown", "value"),
    State("event-dropdown", "value"),
    )   
def display_graph_initial(data, sta, ev):

    # if data is None:
    #     raise dash.exceptions.PreventUpdate
    if any_none(data[ev], sta, ev):
        return dash.no_update

    tf = data[ev][sta]["snr"]

    marks = get_marks(
        data[ev][sta]["min f"], 
        data[ev][sta]["max f"]
        )

    fig = make_fig(
        np.array(data[ev][sta]["sf"]), 
        np.array(data[ev][sta]["sa"]),
        np.array(data[ev][sta]["nf"]), 
        np.array(data[ev][sta]["na"]),
        tf,
        (data[ev][sta]["min bf"], 
         data[ev][sta]["max bf"]),
        )

    return (
        fig, 
        (data[ev][sta]["min bf"], data[ev][sta]["max bf"]),
        not tf, # turns off the range slider if it can't be modeled
        data[ev][sta]["min f"], 
        data[ev][sta]["max f"], 
        marks, 
        tf,
        f"{data[ev][sta]['meta']['repi']:.2f}", 
        f"{data[ev][sta]['meta']['rhyp']:.2f}"
        )


@app.callback(
    Output("graph", "figure"),
    Input("slider-position", "value"),
    [State("graph", "figure"),
     State("store", "data"),
     State("station-dropdown", "value"),
     State("event-dropdown", "value"),   
    ])
def display_graph_update(npos, fig, data, sta, ev):

    if not any_none(npos, fig, data, sta, ev):

        fig = go.Figure(fig)

        if data[ev][sta]["snr"]:
           
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
    Input('commit-change', "n_clicks"),
    [
     State("alert-auto", "is_open"),
     State("event-dropdown", "value"),
     State("store", "data")
    ]
    )
def commit_updates_and_save(n, is_open, ev, data):

    if not any_none(n, is_open, data):

        if n and data is not None:
        
            write_specs(Events.__path__._path[0], data)

            msg = f"Saved spectra for {[ev for ev in data.keys()]}."
            
            if is_open:
                is_open = False

            return msg, (not is_open)
    
    return dash.no_update

if __name__ == '__main__':
    app.run_server(debug=True)