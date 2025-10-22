from GOES_utils import goes_utils as g_utils

year = 2025
month = 6
day = 25
hour = 6
ten_minutes = 0
band = '14'
sat = 'goes19'
latitude_north = 61
latitude_south = 30
longitude_west = -80
longitude_east = -25

ds = g_utils.get_goes_data(band, sat, year, month, day, hour, ten_minutes)
ds = g_utils.get_region_by_lat_lon(ds, latitude_south, latitude_north, longitude_west, longitude_east)

g_utils.plot_band_brightness_temp(ds, fig_dir="GOES_plots", fig_name="goes_example", 
    longitude_west=longitude_west, longitude_east=longitude_east, 
    latitude_south=latitude_south, latitude_north=latitude_north)