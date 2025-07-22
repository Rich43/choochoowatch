from geopy.geocoders import Nominatim


def get_crossing_coords(postcode: str):
    geo = Nominatim(user_agent="train-warn")
    loc = geo.geocode(postcode + ", UK")
    if loc is None:
        raise ValueError("Could not locate postcode")
    return (loc.latitude, loc.longitude)
