import os
import io
import warnings
from tqdm import tqdm
import json
import time
import random
import numpy as np
import matplotlib.pyplot as plt
import cartopy
import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader
import cartopy.io.img_tiles as cimgt
from netCDF4 import Dataset
import multiprocessing
from datetime import datetime
from PIL import Image

CORES = os.cpu_count()

class Merra_cdf4(dict):
    def __init__(self, *args, **kwargs):
        super(Merra_cdf4, self).__init__(*args, **kwargs)
        self.__dict__ = self
        self.lats = None
        self.lons = None
        self.fp = None
        self.file_list("T2M")
        self.lats_lons()
        self.memmap_file_reduced = f"{self.dataset}_reduced_{self.days_count_in_meanslice}.bin"
        self.mean_memmap()
        self.years = np.array([int(year[0]) for year in np.array_split(self.times,
                               self.times.shape[0]//self.days_count_in_meanslice)])
        self.years_unique = [int(year) for year in np.unique(self.years)]
        self.google_merc = ccrs.Mercator(central_longitude=0.0, min_latitude=-80.0,
                                max_latitude=84.0, globe=None, latitude_true_scale=None,
                                false_easting=0.0, false_northing=0.0, scale_factor=None).GOOGLE


    def return_dataset(self, fname):
        with Dataset(fname, mode='r') as data:
            return data.variables[self.dataset][:,:,:]


    def file_list(self, data_folder):
        self.nc_files = {}
        def iter_files():
            for root, dirs, files in os.walk(os.path.join(os.getcwd(), data_folder)):
                for fname in files:
                    if fname[-4:].lower() == '.nc4' or fname[-3:].lower() == '.nc':
                        yield os.path.join(root, fname)

        self.nc_files = np.array(sorted(list(iter_files())), dtype=str)


    def mean_memmap(self):
        with Dataset(self.nc_files[0]) as d:
            shape = (d.dimensions[self.time].size,d.dimensions[self.latitude].size,d.dimensions[self.longitude].size)
        chunks = np.array_split(self.nc_files, self.nc_files.shape[0]//self.days_count_in_meanslice)
        if not os.path.isfile(self.memmap_file_reduced):
            self.mean_chunks = np.memmap(self.memmap_file_reduced, dtype='float32', mode='w+',
                                         shape=(len(chunks),shape[1],shape[2]))
            for index, chunk in enumerate(tqdm(chunks)):
                shapes = [(Dataset(nc_pack).dimensions[self.time].size,
                           Dataset(nc_pack).dimensions[self.latitude].size,
                           Dataset(nc_pack).dimensions[self.longitude].size) for nc_pack in chunk]
                seek = 0
                results = np.empty((len(chunk)*24,shapes[0][1],shapes[0][2]))
                for fname in chunk:
                    result = self.return_dataset(fname)
                    results[seek:seek+result.shape[0]] = result
                    seek += result.shape[0]
                self.mean_chunks[index] = np.mean(results, axis=(0))
            self.mean_chunks.flush()
        self.mean_chunks = np.memmap(self.memmap_file_reduced, dtype='float32', mode='r+',
                                     shape=(len(chunks),shape[1],shape[2]))


    def unpack_time(self):
        for nc_pack in self.nc_files:
            with Dataset(nc_pack) as data:
                year = data.RangeBeginningDate.split('-')[0]
                yield year


    def lats_lons(self):
        with Dataset(self.nc_files[0]) as d:
            self.lats = d.variables[self.latitude][:]
            self.lons = d.variables[self.longitude][:]
        self.times = np.array(list(self.unpack_time()))


    def sliding_window_map_for_flask(self, year_s, year_e):
        mean_s = np.mean(self.mean_chunks[(self.years >= year_s) & (self.years < year_s+4)], axis=(0))
        mean_e = np.mean(self.mean_chunks[(self.years <= year_e) & (self.years > year_e-4)], axis=(0))
        return mean_e - mean_s


    def point_diff(self, lat, lon, year_s, year_e):
        index_lat = np.abs(self.lats-lat).argmin()
        index_lon = np.abs(self.lons-lon).argmin()
        z_dim = self.mean_chunks[:,index_lat, index_lon]
        mean_s = np.mean(z_dim[(self.years >= year_s) & (self.years < year_s+4)])
        mean_e = np.mean(z_dim[(self.years <= year_e) & (self.years > year_e-4)])
        return float(mean_e - mean_s)


    def gen_slide_main(self, year_s, year_e):
        results = self.sliding_window_map_for_flask(year_s, year_e)
        self.clevs = np.arange(-6.0,6.0,0.02)
        fig = plt.figure(figsize=(20.48,15.36), frameon=False)
        ax = plt.axes(projection=self.google_merc)
        ax.set_extent([-180, 180, -90, 90], self.google_merc)
        ax.set_global()
        ax.coastlines(resolution="10m",linewidth=0.5)
        ax.gridlines(linestyle='--',color='black', draw_labels=False)
        plt.contourf(self.lons, self.lats, results, self.clevs, transform=ccrs.PlateCarree(), cmap=plt.cm.seismic)
        fig.savefig(f"./images/mean_changes/{year_s}_{year_e}.jpg", format='jpg',
                    dpi=200, bbox_inches='tight', transparent=False, pad_inches=0)


    def gen_slide(self, year_s, year_e):
        p = multiprocessing.Process(name=f"{year_s}_{year_e}", target=self.gen_slide_main, args=([year_s, year_e]))
        p.start()
        p.join()


    def __del__(self):
        try:
            plt.close()
        except TypeError:
            pass

if __name__ == "__main__":
    et = Merra_cdf4("lat", "lon")
    start_time = time.time()
    et.gen_slide(1985,2018)
    print(time.time()-start_time)

    #et.prep_ax()
