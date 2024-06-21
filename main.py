from typing import List

import requests

GSRN_LJ = "383111580012059894"
gsrn_mt_lj = "383111580118391706"
GSRN_ANK = "383111580022085210"
gsrn_mt_ank = "383111580134839794"

EIMM_LJ = "3-81656"
EIMM_ANK = "7-112779"


def get_data_from_mojelektro(
    api_key: str, endpoint: str, parameters: dict | None
):
    headers = {
        "X-API-TOKEN": f"{api_key}",
        "accept": "application/json",
    }
    if parameters != None:
        response = requests.get(endpoint, headers=headers, params=parameters)

        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()
    else:
        response = requests.get(endpoint, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()


def main():
    EIMM = EIMM_ANK
    gsrn = gsrn_mt_ank
    api_key = "e9d52de2bb9e46e991b30ab4095e76f9"
    meter_readings = "https://api.informatika.si/mojelektro/v1/meter-readings"  # ?startTime=%7B%7D&endTime=%7B%7D'
    merilno_mesto = (
        f"https://api.informatika.si/mojelektro/v1/merilno-mesto/{EIMM}"
    )
    merilna_tocka = (
        f"https://api.informatika.si/mojelektro/v1/merilna-tocka/{gsrn}"
    )
    # meter_readings = "https://test.informatika.si/mojelektro/v1/meter-readings"
    meter_q = "https://api.informatika.si/mojelektro/v1/reading-qualities"
    meter_t = "https://api.informatika.si/mojelektro/v1/reading-type"

    try:
        params = None
        params = {
            "usagePoint": EIMM_LJ,
            "startTime": "2024-05-01",
            "endTime": "2024-06-01",
            "option": [
                "ReadingType=32.0.2.4.1.2.12.0.0.0.0.0.0.0.0.3.72.0",
                "ReadingType=32.0.2.4.1.2.37.0.0.0.0.0.0.0.0.3.38.0",
            ],
        }
        user_data = get_data_from_mojelektro(api_key, meter_readings, params)
        # for k, v in user_data.items():
        #     print(k)
        #     print(v)
        # for oo in user_data:
        #     print(oo)

        # print(user_data)
        data = {}
        for k in user_data["intervalBlocks"]:
            for l in k["intervalReadings"]:
                if l["timestamp"] not in data:
                    data[l["timestamp"]] = {}
                data[l["timestamp"]].update({k["readingType"]: l["value"]})
        print(data)

    except Exception as e:
        print(f"Prišlo je do napake: {e}")


if __name__ == "__main__":
    main()
