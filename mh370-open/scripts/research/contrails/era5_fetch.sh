#!/bin/sh
D=data/research/era5
B=https://storage.googleapis.com/gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3
for t in 1000890 1000891 1000895 1000896; do
 for v in temperature specific_humidity; do
  [ -s $D/$v.$t ] || curl -s -m 600 -o $D/$v.$t "$B/$v/$t.0.0.0"
 done
 for v in high_cloud_cover total_cloud_cover; do
  [ -s $D/$v.$t ] || curl -s -m 120 -o $D/$v.$t "$B/$v/$t.0.0"
 done
done
for v in level latitude longitude; do curl -s -o $D/$v.0 "$B/$v/0"; done
ls -la $D
