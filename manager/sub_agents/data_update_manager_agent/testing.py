import pandas as pd

timestamp = 1721260800000
date = pd.to_datetime(timestamp, unit='ms')
print(date)