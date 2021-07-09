import os
import asyncio
from cdfmap import Merra_cdf4
import multiprocessing
try:
    import ujson as json
except ModuleNotFoundError:
    import json

class flaskerrors(Exception):
    pass


class error_404(flaskerrors):
    def __init__(self):
        self.code = 404


class error_400(flaskerrors):
    def __init__(self):
        self.code = 400


class LeafBackend():
    def __init__(self):
        with open("settings.json", 'r') as f:
            self.config = json.loads(f.read())
        self.merra = Merra_cdf4(self.config)
        os.makedirs(os.path.join("images","mean_changes"), exist_ok=True)



    def values(self, kwargs):
        args = {}
        try:
            args["lat"]=float(kwargs["lat"])
            args["lon"]=float(kwargs["lon"])
            args["year_s"]=int(kwargs["fromdate"])
            args["year_e"]=int(kwargs["todate"])
        except (KeyError, IndexError, ValueError, TypeError) as err:
            raise error_400()
        except Exception as err:
            raise error_400()

        if args["year_s"] > args["year_e"]:
            raise error_400()
        if args["year_s"] not in self.merra.years_unique:
            raise error_400()
        if args["year_e"] not in self.merra.years_unique:
            raise error_400()
        if args["lat"] < -90 or args["lat"] > 90:
            raise error_400()
        if args["lon"] < -180 or args["lon"] > 180:
            raise error_400()

        diff = self.merra.point_diff(**args)
        result = {"result": True, "diff": diff}
        return result


    def overlay(self, kwargs):
        args = {}
        try:
            args["year_s"]=int(kwargs["fromdate"])
            args["year_e"]=int(kwargs["todate"])
        except (KeyError, IndexError, ValueError, TypeError) as err:
            raise error_400()
        except Exception as err:
            raise error_400()

        if args["year_s"] > args["year_e"]:
            raise error_400()
        if args["year_s"] not in self.merra.years_unique:
            raise error_400()
        if args["year_e"] not in self.merra.years_unique:
            raise error_400()

        path = os.path.join(os.getcwd(), "images", f'{args["year_s"]}_{args["year_e"]}.jpg')
        if os.path.isfile(path):
            result = {"result": True}
        else:
            result = {"result": False}

        return result


    def images(self, path):
        try:
            year_s = path.split('/')[-1].split(".")[0].split("_")[0]
            year_e = path.split('/')[-1].split(".")[0].split("_")[1]
            year_s = int(year_s)
            year_e = int(year_e)
        except (KeyError, IndexError, ValueError, TypeError) as err:
            raise error_404()

        if year_s > year_e:
            raise error_404()
        if year_s not in self.merra.years_unique:
            raise error_404()
        if year_e not in self.merra.years_unique:
            raise error_404()

        while f"{year_s}_{year_e}" in [p.name for p in multiprocessing.active_children()]:
            asyncio.sleep(0.1)

        if not os.path.isfile(f"./images/{path}"):
            try:
                self.merra.gen_slide(year_s, year_e)
            except Exception as err:
                raise error_400()



