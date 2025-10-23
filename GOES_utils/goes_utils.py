import xarray as xr
import netCDF4
import datetime
import s3fs
import requests
import fnmatch
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy.crs as ccrs
import cartopy.feature as feature
import numpy as np
import os

def get_goes_data(band, sat, year, month, day, hour, ten_minutes):
    """
    band : str, include the leading zero, '14' 
    sat : str, 'goes19'
    ten_minutes: int, zero for top-of-the-hour
    """

    julian_day = datetime.datetime(year, month, day).strftime('%j')
    print(julian_day)

    datetime_str = str(year)+'-'+str(month).zfill(2)+'-'+str(day).zfill(2)+' '+str(hour).zfill(2)+'Z'
    print(datetime_str)

    fs = s3fs.S3FileSystem(anon=True)

    bucket = f'noaa-{sat}'
    product = 'ABI-L1b-RadF' #---Full disk ABI radiance

    data_path = bucket + '/' + product + '/'  + str(year) + '/' + julian_day + '/' + str(hour).zfill(2)

    files = fs.ls(data_path)

    files_band = [file for file in files if fnmatch.fnmatch(file.split('/')[-1], 'OR_ABI-L1b-RadF-M6C' + band + '*')]
    file = files_band[ten_minutes]
    print(file)
    resp = requests.get(f'https://'+bucket+'.s3.amazonaws.com/'+file[12:])
    if str(resp) != '<Response [200]>':
        print('b07 file not found in AWS servers')

    nc = netCDF4.Dataset(file, memory = resp.content)
    ds = xr.open_dataset(xr.backends.NetCDF4DataStore(nc))

    return ds

def calc_latlon(ds):
    # The math for this function was taken from 
    # https://makersportal.com/blog/2018/11/25/goes-r-satellite-latitude-and-longitude-grid-projection-algorithm
    x = ds.x
    y = ds.y
    goes_imager_projection = ds.goes_imager_projection
    
    x,y = np.meshgrid(x,y)
    
    r_eq = goes_imager_projection.attrs["semi_major_axis"]
    r_pol = goes_imager_projection.attrs["semi_minor_axis"]
    l_0 = goes_imager_projection.attrs["longitude_of_projection_origin"] * (np.pi/180)
    h_sat = goes_imager_projection.attrs["perspective_point_height"]
    H = r_eq + h_sat
    
    a = np.sin(x)**2 + (np.cos(x)**2 * (np.cos(y)**2 + (r_eq**2 / r_pol**2) * np.sin(y)**2))
    b = -2 * H * np.cos(x) * np.cos(y)
    c = H**2 - r_eq**2
    
    #--- Added absolute to remove error
    r_s = (-b - np.sqrt(np.absolute(b**2 - 4*a*c)))/(2*a)
    
    s_x = r_s * np.cos(x) * np.cos(y)
    s_y = -r_s * np.sin(x)
    s_z = r_s * np.cos(x) * np.sin(y)
    
    lat = np.arctan((r_eq**2 / r_pol**2) * (s_z / np.sqrt((H-s_x)**2 +s_y**2))) * (180/np.pi)
    lon = (l_0 - np.arctan(s_y / (H-s_x))) * (180/np.pi)
    
    ds = ds.assign_coords({
        "lat":(["y","x"],lat),
        "lon":(["y","x"],lon)
    })
    ds.lat.attrs["units"] = "degrees_north"
    ds.lon.attrs["units"] = "degrees_east"
    return ds

def get_xy_from_latlon(ds, lats, lons):
    lat1, lat2 = lats
    lon1, lon2 = lons

    lat = ds.lat.data
    lon = ds.lon.data
    
    x = ds.x.data
    y = ds.y.data
    
    x,y = np.meshgrid(x,y)
    
    x = x[(lat >= lat1) & (lat <= lat2) & (lon >= lon1) & (lon <= lon2)]
    y = y[(lat >= lat1) & (lat <= lat2) & (lon >= lon1) & (lon <= lon2)] 
    
    return ((min(x), max(x)), (min(y), max(y)))

def get_region_by_lat_lon(ds, extent):
    """
    ds : from get_goes_data()
    extent : lat/lon, [west, east, south, north]
    """
    ds_lat_lon = calc_latlon(ds)
    #---This is needed to convert the lat/lon range into the x/y dimensions
    #------The dataset will only filter by the official dimensions
    ((x1,x2), (y1, y2)) = get_xy_from_latlon(ds_lat_lon, (extent[2], extent[3]), (extent[0], extent[1]))
    region = ds_lat_lon.sel(x=slice(x1, x2), y=slice(y2, y1))
    return region

def plot_band_brightness_temp(ds, fig_dir, fig_name, extent):
    """
    ds : from get_goes_data()
    extent : lat/lon, [west, east, south, north]
    """
    wl = round(ds.band_wavelength.values[0],1)
    Tb = (ds.planck_fk2/(np.log((ds.planck_fk1/ds.Rad)+1)) - ds.planck_bc1)/ds.planck_bc2

    projection=ccrs.PlateCarree(central_longitude=0)
    fig,ax=plt.subplots(1, figsize=(12,12),subplot_kw={'projection': projection})

    levels = np.linspace(200, 300, 30)
    c=ax.contourf(Tb.lon, Tb.lat, Tb, cmap='Greys', extend='both', levels=levels)

    clb = plt.colorbar(c, shrink=0.4, pad=0.02, ax=ax)
    clb.ax.tick_params(labelsize=15)
    clb.set_label('(K)', fontsize=15)

    custom_ticks = [290, 270, 250, 230, 210]
    clb.set_ticks(custom_ticks)

    #--- Remove for full-scan
    ax.set_extent(extent, crs=ccrs.PlateCarree())

    ax.set_title("GOES Brightness Temperature ("+ str(wl) +" μm) \n(<datetime> UTC)", fontsize=20, pad=10)
    ax.coastlines(resolution='50m', color='black', linewidth=1)
    #ax.add_feature(feature.LAND, zorder=100, edgecolor='#000', facecolor='#DABC94')
    ax.add_feature(feature.STATES, edgecolor='white', linewidth=1, zorder=6)

    _plt_save(fig_dir, fig_name)
    return

def _plt_save(fig_dir, fig_name):
    os.makedirs(f"{fig_dir}", exist_ok=True)
    plt.savefig(f"{fig_dir}/{fig_name}.png", dpi=200, bbox_inches='tight')
    plt.close()

def plot_btd(ds1, ds2, fig_dir, fig_name, extent, plot_title):
    """
    ds : from get_goes_data()
    extent : lat/lon, [west, east, south, north]
    """

    #--- Calculate BTD, ds1 - ds2
    wl1 = round(ds1.band_wavelength.values[0],1)
    Tb1 = (ds1.planck_fk2/(np.log((ds1.planck_fk1/ds1.Rad)+1)) - ds1.planck_bc1)/ds1.planck_bc2

    wl2 = round(ds2.band_wavelength.values[0],1)
    Tb2 = (ds2.planck_fk2/(np.log((ds2.planck_fk1/ds2.Rad)+1)) - ds2.planck_bc1)/ds2.planck_bc2

    btd = Tb1 - Tb2

    #--- Plot BTD 
    projection=ccrs.PlateCarree(central_longitude=0)
    fig,ax=plt.subplots(1, figsize=(12,12),subplot_kw={'projection': projection})

    cmap = mcolors.LinearSegmentedColormap.from_list(
        "custom_cmap",
        [(0, "#06BA63"), (0.5, "black"), (1, "white")]
    )
    norm = mcolors.TwoSlopeNorm(vmin=-6, vcenter=0, vmax=1.5)

    pcm = plt.pcolormesh(btd.lon, btd.lat, btd, cmap=cmap, norm=norm, shading="nearest")

    clb = plt.colorbar(pcm, shrink=0.6, pad=0.02, ax=ax)
    clb.ax.tick_params(labelsize=15)
    clb.set_label('(K)', fontsize=15)

    if extent: ax.set_extent(extent, crs=ccrs.PlateCarree())
    ax.set_title(plot_title, fontsize=20, pad=10)
    ax.coastlines(resolution='50m', color='black', linewidth=1)

    _plt_save(fig_dir, fig_name)
    return

def create_formatted_srf(srf_file, filename):
    """
    Puts GOES ABI SRF into format used by VIIRS, so it can be used by cris_utils and modtran_utils
    """
    srf = np.loadtxt(srf_file)
    x = srf[:, 0]*1000
    y = srf[:, 2]

    with open(f"{filename}.dat", "w") as f:
        for xi, yi in zip(x, y):
            f.write(f"{xi} {yi}\n")

    return