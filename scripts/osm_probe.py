import logging, sys, time
logging.basicConfig(level=logging.INFO)
from hytte_finder import osm
t = time.time()
r = osm.analyse(61.1527, 10.69)
print(round(time.time() - t), "s")
for k, v in r.items():
    print(k, v)
