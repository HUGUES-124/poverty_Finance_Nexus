"""Optional: pre-download the district boundaries (the app also does this automatically)."""
import os, sys, requests
URL = ("https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/9469f09592ced973a3448cf66b6100b741b64c0d/"
       "releaseData/gbOpen/RWA/ADM2/geoBoundaries-RWA-ADM2_simplified.geojson")
out = os.path.join(os.path.dirname(__file__), "..", "static", "data", "rwanda_districts.geojson")
r = requests.get(URL, timeout=60); r.raise_for_status()
open(out, "wb").write(r.content); print("saved", out, len(r.content), "bytes")
