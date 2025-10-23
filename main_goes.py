from GOES_utils import goes_utils as g_utils

year = 2025
month = 3
day = 12
hour = 6
ten_minutes = 4
band1, wl1 = '14', 11.2
band2, wl2 = '07', 3.9
sat = 'goes19'
extent=[-73, -57, 33, 46]

ds1 = g_utils.get_goes_data(band1, sat, year, month, day, hour, ten_minutes)
ds1 = g_utils.get_region_by_lat_lon(ds1, extent)

ds2 = g_utils.get_goes_data(band2, sat, year, month, day, hour, ten_minutes)
ds2 = g_utils.get_region_by_lat_lon(ds2, extent)

# g_utils.plot_band_brightness_temp(ds1, fig_dir="GOES_plots", 
#     fig_name="goes_example", extent=extent)

fig_name = f"{sat}_{band1}-{band2}_{year}{month:02}{day:02}_{hour:02}{ten_minutes}0"
plot_title = f"ABI B{band1} - B{band2} ({wl1} µm - {wl2} µm) BTD \n {sat} d{year}{month:02}{day:02} t{hour:02}{ten_minutes}0"

g_utils.plot_btd(ds1, ds2, fig_dir="GOES_plots", fig_name=fig_name, 
    extent=extent, plot_title=plot_title)