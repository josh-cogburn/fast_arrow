from fast_arrow.api_requestor import get
from fast_arrow.util import chunked_list


class Option(object):

    @classmethod
    def fetch(cls, bearer, _id):
        """
        fetch instrument by _id
        """
        return cls.fetch_list(bearer, [_id])[0]


    @classmethod
    def fetch_list(cls, bearer, ids):
        """
        fetch instruments by ids
        """
        param_ids = ",".join(ids)
        params = {"ids": param_ids}

        url = "https://api.robinhood.com/options/instruments/"
        data = get(url, bearer=bearer, params=params)
        results = data["results"]

        while data["next"]:
            data = get(data["next"], bearer=bearer)
            results.extend(data["results"])
        return results


    @classmethod
    def marketdata(cls, bearer, _id):
        """
        fetch marketdata for option instrument
        (eg, Delta, Theta, Rho, Vega, Open Interest)
        """
        return cls.marketdata_list(bearer, [_id])[0]


    @classmethod
    def marketdata_list(cls, bearer, ids):
        """
        fetch marketdata for option instrument
        (eg, Delta, Theta, Rho, Vega, Open Interest)
        """
        # build params
        base_marketdata_url = "https://api.robinhood.com/options/instruments/"
        id_urls = []
        for _id in ids:
            id_url = "{}{}/".format(base_marketdata_url, _id)
            id_urls.append(id_url)

        instruments = ",".join(id_urls)
        params = {"instruments": instruments}

        # fetch
        url = "https://api.robinhood.com/marketdata/options/"
        data = get(url, bearer=bearer, params=params)
        results = data["results"]

        if "next" in data:
            while(data["next"]):
                data = get(data["next"], bearer=bearer)
                results.extend(data["results"])
        return results


    @classmethod
    def in_chain(cls, bearer, chain_id, expiration_dates=[]):
        """
        fetch all option instruments in an options chain
        - expiration_dates = optionally scope
        """
        assert(type(expiration_dates) is list)

        url = "https://api.robinhood.com/options/instruments/"
        params = {
            "chain_id": chain_id
        }
        if len(expiration_dates) > 0:
            params["expiration_dates"] = ",".join(expiration_dates)

        data = get(url, bearer=bearer, params=params)
        results = data['results']
        while data['next']:
            data = get(data['next'], bearer=bearer)
            results.extend(data['results'])
        return results


    @classmethod
    def merge_marketdata(cls, bearer, options, humanize=True):
        ids = [x["id"] for x in options]

        mds = []
        for chunk_ids in chunked_list(ids, 50):
            mds_chunk = cls.marketdata_list(bearer, chunk_ids)
            mds.extend(mds_chunk)

        results = []
        for o in options:
            # @TODO optimize this so it's better than O(n^2)
            md = [md for md in mds if md['instrument'] == o['url']][0]
            # there is overlap in keys, so it's fine to do a merge
            merged_dict = dict( list(o.items()) + list(md.items()) )
            results.append(merged_dict)

        return results
