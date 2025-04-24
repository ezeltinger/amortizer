import dash
from dash import dcc, html, Input, Output, State, dash_table
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import webbrowser
from waitress import serve


app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Amortization Schedule with Lump Sum Payments"),

    html.Div([
        html.Label("Loan Amount:"),
        dcc.Input(id='loan-amount', type='number', value=300000),

        html.Label("Annual Interest Rate (%):"),
        dcc.Input(id='interest-rate', type='number', value=5, step=0.01),

        html.Label("Loan Term (Years):"),
        dcc.Input(id='loan-term', type='number', value=30),

        html.Label("Start Month (MM/YYYY):"),
        dcc.Input(id='start-month', type='text', value='04/2024'),

        html.Label("Original Home Value:"),
        dcc.Input(id='home-value', type='number', value=375000),

        html.Label("Percentage Equity to Highlight (%):"),
        dcc.Input(id='equity-percentage', type='number', value=20, step=0.1),
    ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(2, 1fr)', 'gap': '10px'}),

    html.Div([
        html.Label("Lump Sum Payments (Month:Amount, comma-separated, e.g., 12:1000,24:500):"),
        dcc.Input(id='lump-sum-payments', type='text', value=''),
    ], style={'marginTop': '20px'}),

    dcc.Graph(id='amortization-graph'),
    dash_table.DataTable(id='amortization-table', page_size=10, style_table={'overflowX': 'auto'})
])

def calculate_amortization(loan_amount, annual_rate, years, lump_payments, start_date, home_value, equity_percentage):
    monthly_rate = annual_rate / 100 / 12
    months = years * 12
    monthly_payment = loan_amount * monthly_rate / (1 - (1 + monthly_rate) ** -months)

    balance = loan_amount
    schedule = []
    date = start_date
    paid_off_equity = None

    for month in range(1, months + 1):
        interest = balance * monthly_rate
        principal = monthly_payment - interest
        balance -= principal

        if month in lump_payments:
            balance -= lump_payments[month]
            principal += lump_payments[month]

        if not paid_off_equity and balance <= home_value * (1 - equity_percentage / 100):
            paid_off_equity = date

        if balance < 0:
            principal += balance
            balance = 0

        schedule.append({
            'Date': date,
            'Interest': round(interest, 2),
            'Principal': round(principal, 2),
            'Balance': round(balance, 2)
        })

        if balance <= 0:
            break

        # Move to next month
        if date.month == 12:
            date = datetime(date.year + 1, 1, 1)
        else:
            date = datetime(date.year, date.month + 1, 1)

    df = pd.DataFrame(schedule)
    return df, paid_off_equity

@app.callback(
    [Output('amortization-graph', 'figure'), Output('amortization-table', 'data'), Output('amortization-table', 'columns')],
    [Input('loan-amount', 'value'),
     Input('interest-rate', 'value'),
     Input('loan-term', 'value'),
     Input('lump-sum-payments', 'value'),
     Input('start-month', 'value'),
     Input('home-value', 'value'),
     Input('equity-percentage', 'value')]
)
def update_graph(loan_amount, interest_rate, loan_term, lump_sum_input, start_month, home_value, equity_percentage):
    try:
        start_date = datetime.strptime(start_month, "%m/%Y")
    except ValueError:
        return {}, [], []

    lump_payments = {}
    if lump_sum_input:
        for entry in lump_sum_input.split(','):
            try:
                month, amt = entry.split(':')
                lump_payments[int(month)] = float(amt)
            except:
                continue

    df, paid_off_equity = calculate_amortization(loan_amount, interest_rate, loan_term, lump_payments, start_date, home_value, equity_percentage)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Balance'], mode='lines+markers', name='Balance'))

    if paid_off_equity:
        fig.add_vline(
            x=paid_off_equity.timestamp() * 1000,
            line=dict(color='red', dash='dash'),
            annotation_text=f"{equity_percentage}% Equity Reached",
            annotation_position="top left"
        )

    fig.update_layout(
        title="Amortization Schedule",
        xaxis_title="Date",
        yaxis_title="Balance"
    )
    fig.update_xaxes(tickformat="%b %Y")

    df_display = df.copy()
    df_display['Date'] = df_display['Date'].dt.strftime('%b %Y')

    columns = [{'name': col, 'id': col} for col in df_display.columns]
    return fig, df_display.to_dict('records'), columns

def open_browser():
    """Open the default web browser."""
    webbrowser.open("http://127.0.0.1:8050/", new=2)

if __name__ == '__main__':
    open_browser()
    # Run the Dash app
    serve(app.server, host="127.0.0.1", port=8050)
