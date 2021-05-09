import streamlit
import ftxclient

import datetime
import pytz
import pandas
import time

def annualized_basis(underlying, now, ftx_client):
    underlying = underlying.upper()

    underlying_information = ftx_client.get_market(f'{underlying}/USD')
    underlying_px = (underlying_information['bid'] + underlying_information['ask']) / 2.

    futures = ftx_client.get_futures()
    contracts = filter(lambda future: future['underlying'] == underlying and \
                                            future['type'] == 'future',
                        futures)

    results = {}
    for contract in contracts:
        futures_px = (contract['bid'] + contract['ask']) / 2.
        expiration_date = pandas.Timestamp(contract['expiry'])

        delta = expiration_date - now

        annualized_premia = (futures_px / underlying_px) ** (pandas.Timedelta(days = 365.25) / delta) - 1

        results[delta / pandas.Timedelta(days = 365.25)] = annualized_premia

    return pandas.Series(results).sort_index()


def main():
    streamlit.title("FTX Cash + Carry Information")

    premia_chart = None
    forward_chart = None

    while True:
        ftx_client = ftxclient.FtxClient()
        now = datetime.datetime.now(pytz.utc)

        annualized_premia = {}
        forward_rates = {}

        for underlying in ['BTC', 'ETH']: #'SOL'
            premia = annualized_basis(underlying, now, ftx_client)

            annualized_premia[underlying] = premia

            x = (1. + premia) ** (premia.index)
            x = x / x.shift(1) - 1
            forward_rate = (1 + x.iloc[1:]) ** (1 / (x.index[1:] - x.index[0:-1])) - 1
            
            forward_rates[underlying] = forward_rate

        annualized_premia = pandas.DataFrame(annualized_premia)
        if premia_chart is None:
            streamlit.subheader('Annualized Premia')
            premia_chart = streamlit.line_chart(annualized_premia)

        else: 
            premia_chart.line_chart(annualized_premia)

        forward_rates = pandas.DataFrame(forward_rates)
        if forward_chart is None:
            streamlit.subheader('Forward Rates')
            forward_chart = streamlit.line_chart(forward_rates)

        else: 
            forward_chart.line_chart(forward_rates)

        time.sleep(5)




if __name__ == "__main__":
    main()