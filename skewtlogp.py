import numpy as np
import datetime
from client import GribStreamClient
import numpy as np
import matplotlib.pyplot as plt
from metpy.plots import SkewT
from metpy.units import units

pressure_levels = [
    100, 125, 150, 175, 200, 225, 250, 275, 300, 325, 350, 375, 400,
    425, 450, 475, 500, 525, 550, 575, 600, 625, 650, 675, 700, 725,
    750, 775, 800, 825, 850, 875, 900, 925, 950, 975, 1000
]

names = ['TMP', 'RH', 'UGRD', 'VGRD', 'HGT']

variables = []
for name in names:
    for p in pressure_levels:
        variables.append({'name': name, 'level': f'{p} mb', 'info': ''})

dt = datetime.datetime(year=2025, month=1, day=1, hour=0)
coords = {"lat": 29.749907, "lon": -95.358421}
city = 'Houston, TX'

with GribStreamClient() as client:
    df = client.history(
        dataset='rap',
        from_time=dt,
        until_time=dt+datetime.timedelta(hours=1),
        min_horizon=0,
        max_horizon=55,
        coordinates=[coords],
        variables=variables,
    )

# Example row to plot (replace with desired row selection)
row = df.iloc[0]

# Extract temperature, dewpoint, and pressure
temperature = np.array([row[f'TMP|{p} mb|'] for p in pressure_levels]) * units.kelvin
relative_humidity = np.array([row[f'RH|{p} mb|'] for p in pressure_levels]) * units.percent
pressure = np.array(pressure_levels) * units.hPa
geopotential_height = np.array([row[f'HGT|{p} mb|'] for p in pressure_levels]) * units.meter

# Calculate dewpoint temperature from relative humidity and temperature
from metpy.calc import dewpoint_from_relative_humidity
dewpoint = dewpoint_from_relative_humidity(temperature, relative_humidity)

# Create the Skew-T plot
fig = plt.figure(figsize=(9, 9))
skew = SkewT(fig, rotation=45)

# Plot temperature and dewpoint
skew.plot(pressure, temperature.to('degC'), 'r', label='Temperature')
skew.plot(pressure, dewpoint.to('degC'), 'g', label='Dewpoint')

# Add wind barbs if U and V wind components are available
try:
    u_wind = np.array([row[f'UGRD|{p} mb|'] for p in pressure_levels]) * units('m/s')
    v_wind = np.array([row[f'VGRD|{p} mb|'] for p in pressure_levels]) * units('m/s')
    skew.plot_barbs(pressure, u_wind, v_wind)
except KeyError:
    print("U and V wind components not available; skipping wind barbs.")

# Add adiabats and mixing ratio lines
skew.plot_dry_adiabats()
skew.plot_moist_adiabats()
skew.plot_mixing_lines()

# Add legend and labels
plt.legend()
plt.title(f"Skew-T Log-P Chart. {city} - {coords} \n\tForecasted at: {row['forecasted_at']} Forecasted time: {row['forecasted_time']}")

plt.show()
