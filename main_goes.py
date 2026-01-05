from GOES_utils import goes_utils as g_utils

year = 2025
month = 3
day = 12
hour = 6
ten_minutes = 4
band1, wl1 = '13', 10.3
band2, wl2 = '07', 3.9
sat = 'goes19'
extent=[-73, -57, 33, 46]

#--- Open GOES ABI data
ds1 = g_utils.get_goes_data(band1, sat, year, month, day, hour, ten_minutes)
ds1 = g_utils.get_region_by_lat_lon(ds1, extent)

ds2 = g_utils.get_goes_data(band2, sat, year, month, day, hour, ten_minutes)
ds2 = g_utils.get_region_by_lat_lon(ds2, extent)

#--- Plot single band
# g_utils.plot_band_brightness_temp(ds1, fig_dir="GOES_plots", 
#     fig_name="goes_example", extent=extent)

#--- Plot brightness temperature difference
fig_name = f"{sat}_{band1}-{band2}_{year}{month:02}{day:02}_{hour:02}{ten_minutes}0"
plot_title = f"ABI B{band1} - B{band2} ({wl1} µm - {wl2} µm) BTD \n {sat} d{year}{month:02}{day:02} t{hour:02}{ten_minutes}0"

g_utils.plot_btd(ds1, ds2, fig_dir="GOES_plots", fig_name=fig_name, 
    extent=extent, plot_title=plot_title, custom_cmap_name="blueblack")

#--- Put SRF file in format for spectral analysis utils
# band = "ch14"
# srf_file = f"ABI_spectral_response_functions/GOES-R_ABI_FM4_SRF_CWG_{band}.txt"
# filename = f"ABI_spectral_response_functions/GOES-R_ABI_SRF_{band}"
# g_utils.create_formatted_srf(srf_file, filename)