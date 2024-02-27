import json

from elasticsearch import Elasticsearch
import math


class Index:
    def __init__(self, config):
        self.config = config
        self.client = Elasticsearch(hosts=[{"host": "raa_es"}], retry_on_timeout=True)
        #self.client = Elasticsearch()

    def no_case(self, str_in):
        str = str_in.strip()
        ret_str = ""
        if (str != ""):
            for char in str:
                ret_str = ret_str + "[" + char.upper() + char.lower() + "]"
        return ret_str + ".*"

    def get_facet(self, field, amount):
        ret_array = []
        response = self.client.search(
            index="raa",
            body=
            {
                "size": 0,
                "aggs": {
                    "names": {
                        "terms": {
                            "field": field,
                            "size": amount,
                            "order": {
                                "_term": "asc"
                            }
                        }
                    }
                }
            }
        )
        for hits in response["aggregations"]["names"]["buckets"]:
            buffer = {"key": hits["key"], "doc_count": hits["doc_count"]}
            ret_array.append(buffer)
        return ret_array

    def get_filter_facet(self, field, amount, facet_filter):
        print(facet_filter)
        ret_array = []
        response = self.client.search(
            index="raa",
            body=
            {
                "query": {
                    "regexp": {
                        field: self.no_case(facet_filter)
                    }
                },
                "size": 0,
                "aggs": {
                    "names": {
                        "terms": {
                            "field": field,
                            "size": amount,
                            "order": {
                                "_count": "desc"
                            }
                        }
                    }
                }
            }
        )
        for hits in response["aggregations"]["names"]["buckets"]:
            buffer = {"key": hits["key"], "doc_count": hits["doc_count"]}
            ret_array.append(buffer)
        return ret_array

    def get_person(self, id):
        response = self.client.search(
            index="raa",
            body={"query": {
                "terms": {
                    "_id": [id]
                }
            },
                "_source": ["voornaam", "tussenvoegsel", "geslachtsnaam", "geboortedatum", "geboorteplaats", "doopjaar", "overlijdensdatum", "overlijdensplaats", "geboortejaar", "overlijdensjaar", "adellijke_titel", "academische_titel", "aanstelling"]
            }
        )
        if response["hits"]["total"]["value"] == 1:
            return response["hits"]["hits"][0]["_source"]
        else:
            return []

    def browse(self, page, length, orderFieldName, searchvalues):
        int_page = int(page)
        start = (int_page - 1) * length
        matches = []

        if searchvalues == []:
            response = self.client.search(
                index="raa",
                body={"query": {
                    "match_all": {}},
                    "_source": ["doopjaar", "geboortejaar", "geboorteplaats", "geslachtsnaam", "overlijdensjaar", "overlijdensplaats", "tussenvoegsel", "voornaam"],
                    "sort": [{"geslachtsnaam.keyword": {"order": "asc"}} ],
                    "size": length,
                    "from": start
                }
            )
        else:
            for item in searchvalues:
                if item["field"] == "FREE_TEXT":
                    for value in item["values"]:
                        matches.append({"multi_match": {"query": value, "fields": ["*"]}})
                else:
                    if len(item["values"]) > 1:
                        matches.append({"terms": {item["field"] + ".keyword": item["values"]}})
                    else:
                        matches.append({"term": {item["field"] + ".keyword": item["values"][0]}})
            response = self.client.search(
                index="raa",
                body={"query": {
                    "bool": {
                        "filter": matches
                    }},
                    "_source": ["doopjaar", "geboortejaar", "geboorteplaats", "geslachtsnaam", "overlijdensjaar", "overlijdensplaats", "tussenvoegsel", "voornaam"],
                    "sort": [{"geslachtsnaam.keyword": {"order": "asc"}}],
                    "size": length,
                    "from": start
                }
            )


        ret_array = {"amount": response["hits"]["total"]["value"],
                     "pages": math.ceil(response["hits"]["total"]["value"] / length), "items": []}
        for item in response["hits"]["hits"]:
            tmp_arr = item["_source"]
            tmp_arr["_id"] = item["_id"]
            ret_array["items"].append(tmp_arr)
        return ret_array
