"""Download real elevation data and save compact npz files for the OUJ video.
Sources: NOAA NCEI ETOPO 2022 (60 arc-second surface) and Copernicus GLO-90 DEM (ESA, AWS open data)."""
import os, sys, urllib.request, numpy as np, rasterio
from rasterio.enums import Resampling

OUT = "fetch/out/ouj"
os.makedirs(OUT, exist_ok=True)

ETOPO = "https://www.ngdc.noaa.gov/thredds/fileServer/global/ETOPO2022/60s/60s_surface_elev_gtif/ETOPO_2022_v1_60s_N90W180_surface.tif"
def get(url, path):
    if not os.path.exists(path):
        print("GET", url, flush=True)
        urllib.request.urlretrieve(url, path)
    return path

etopo = get(ETOPO, "/tmp/etopo60.tif")
with rasterio.open(etopo) as src:
    print(src.width, src.height, src.transform, flush=True)
    # global grid 0.1 deg (3600 x 1800)
    g = src.read(1, out_shape=(1800, 3600), resampling=Resampling.average).astype(np.int16)
    np.savez_compressed(f"{OUT}/etopo_global_0p1.npz", z=g, lat0=90.0, lon0=-180.0, step=0.1)
    full = src.read(1)
    def crop(name, lat1, lat2, lon1, lon2):
        r1 = int(round((90 - lat2) * 60)); r2 = int(round((90 - lat1) * 60))
        c1 = int(round((lon1 + 180) * 60)); c2 = int(round((lon2 + 180) * 60))
        z = full[r1:r2, c1:c2].astype(np.int16)
        np.savez_compressed(f"{OUT}/etopo_{name}.npz", z=z, lat_top=lat2, lon_left=lon1, step=1/60)
        print(name, z.shape, int(z.min()), int(z.max()), flush=True)
    crop("nweurope", 46, 58, -8, 14)
    crop("useast", 36, 46, -80, -66)
    crop("chinaeast", 26, 36, 114, 126)
    crop("indiawest", 14, 24, 68, 78)
    crop("centralasia", 34, 48, 52, 78)
    crop("bangladesh", 20, 27, 86, 94)
    crop("florida", 24, 31.5, -88, -79)

# Copernicus GLO-90 1-degree tiles (3 arc-second) for city close-ups
def tname(lat, lon):
    ns = "N" if lat >= 0 else "S"; ew = "E" if lon >= 0 else "W"
    return f"Copernicus_DSM_COG_30_{ns}{abs(lat):02d}_00_{ew}{abs(lon):03d}_00_DEM"
def city(name, lats, lons, step=2):
    rows = []
    for la in sorted(lats, reverse=True):
        row = []
        for lo in lons:
            t = tname(la, lo)
            url = f"https://copernicus-dem-90m.s3.amazonaws.com/{t}/{t}.tif"
            p = f"/tmp/{t}.tif"
            try:
                get(url, p)
                with rasterio.open(p) as s:
                    a = s.read(1, out_shape=(1200 // step, 1200 // step), resampling=Resampling.average)
            except Exception as e:
                print("ocean/missing", t, e, flush=True)
                a = np.full((1200 // step, 1200 // step), -5.0, np.float32)
            row.append(a)
        rows.append(np.hstack(row))
    z = np.vstack(rows).astype(np.float32)
    z = np.round(z * 10).astype(np.int16)  # decimetres
    np.savez_compressed(f"{OUT}/cop_{name}.npz", z_dm=z, lat_top=max(lats) + 1, lon_left=min(lons), step=step * 3 / 3600)
    print(name, z.shape, z.min() / 10, z.max() / 10, flush=True)

city("london", [51], [-1, 0, 1])
city("netherlands", [51, 52, 53], [3, 4, 5, 6])
city("newyork", [40, 41], [-75, -74, -73])
city("shanghai", [30, 31], [120, 121, 122])
city("mumbai", [18, 19], [72, 73])
city("tashkent", [40, 41], [68, 69, 70])
print("done")
