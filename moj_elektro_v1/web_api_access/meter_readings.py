from datetime import date, datetime, timedelta
from logging import Logger

from moj_elektro_v1.blocks.time_blocks import TimeBlocks
from moj_elektro_v1.http_access.http_JSON_conn import (
    ClientResponse,
    ClientSession,
    HTTPJSONConnection,
)
from moj_elektro_v1.web_api_access.merilna_tocka import MerilnaTocka
from moj_elektro_v1.web_api_access.meter_type import MeterType

dt_fmt = "%Y-%m-%d"
ts_fmt = "%Y-%m-%dT%H:%M:%S%z"


def _last_day_of_month(any_day):
    next_month = any_day.replace(day=28) + timedelta(
        days=4
    )  # this will never fail
    return next_month - timedelta(days=next_month.day)


def _get_param_list(begin, end, EIMM, option_list):
    result = []
    while True:
        if begin.month == 12:
            next_month = begin.replace(year=begin.year + 1, month=1, day=1)
        else:
            next_month = begin.replace(month=begin.month + 1, day=1)
        if next_month > end:
            break
        result.append(
            {
                "usagePoint": f"{EIMM}",
                "startTime": begin.strftime(dt_fmt),
                "endTime": _last_day_of_month(begin).strftime(dt_fmt),
                "option": option_list,
            }
        )
        begin = next_month
    result.append(
        {
            "usagePoint": f"{EIMM}",
            "startTime": begin.strftime(dt_fmt),
            "endTime": end.strftime(dt_fmt),
            "option": option_list,
        }
    )
    return result


def _get_block_dogovorjena_moc(row: dict, dogovorjene_moci: list):
    ret = None
    if dogovorjene_moci is not None and "Blok" in row:
        for dmc in dogovorjene_moci:
            d_f_s = datetime.strptime(dmc["datumOd"], ts_fmt)
            d_t_s = datetime.strptime(dmc["datumDo"], ts_fmt)
            t_s = row["dt"]
            block = row["Blok"]
            if d_f_s <= t_s and t_s < d_t_s:
                if block in dmc:
                    ret = dmc[block]
                    break
    return ret


class MeterReadings(HTTPJSONConnection):
    def __init__(self, api_key: str, logger: Logger | None = None) -> None:
        super().__init__(
            {
                "X-API-TOKEN": f"{api_key}",
                "accept": "application/json",
            },
            "https://api.informatika.si/mojelektro/v1/meter-readings",
            logger,
        )
        self.__time_blocks = TimeBlocks.load_time_block_definitions()

    @classmethod
    async def generate_readings(
        cls,
        session: ClientSession,
        api_key: str,
        EIMM: str,
        frm: date,
        to: date,
        oznaka_list: list,
        logger: Logger | None = None,
    ):
        parameters = await MerilnaTocka.get_parameters_by_vrsta(
            session, api_key, EIMM, logger
        )

        lookup_reading_list = await MeterType.get_reading_type_lookup(
            session, api_key, oznaka_list, parameters, logger
        )

        reading_type_template = "ReadingType={0}"
        option_list = []
        if lookup_reading_list is not None and isinstance(
            lookup_reading_list, dict
        ):
            for reading_type in lookup_reading_list:
                option_list.append(reading_type_template.format(reading_type))
        if len(option_list) > 0:
            param_list = _get_param_list(frm, to, EIMM, option_list)
            for params in param_list:
                data: dict[str, dict] = {}
                mr = cls(api_key, logger)
                readings = await mr(session, params)
                if readings is not None and isinstance(readings, dict):
                    for k in readings["intervalBlocks"]:
                        for l in k["intervalReadings"]:
                            lkp: tuple[str, list, int, int] = (
                                lookup_reading_list.get(
                                    k["readingType"], ("Unknown", [], 0, 0)
                                )
                            )
                            if l["timestamp"] not in data:
                                data[l["timestamp"]] = {}
                                data[l["timestamp"]].update(
                                    {"Merilno mesto": EIMM}
                                )
                                ts = datetime.strptime(l["timestamp"], ts_fmt)
                                ts = ts - timedelta(minutes=15)
                                data[l["timestamp"]].update(
                                    {
                                        "dt": ts,
                                        "Leto": ts.year,
                                        "Mesec": ts.month,
                                        "Dan": ts.day,
                                        "DanVTednu": ts.weekday(),
                                        "Ura": ts.hour,
                                        "Minuta": ts.minute,
                                        "Sekunda": ts.second,
                                    }
                                )
                                slots = await mr.lookup_slots(
                                    data[l["timestamp"]]
                                )
                                if "tarif" in slots and lkp[2] != 2:
                                    slots["tarif"]["slot"] = "ET"

                                if (
                                    "limit" in slots
                                    and "slot" in slots["limit"]
                                ):
                                    data[l["timestamp"]].update(
                                        {
                                            "Blok": slots["limit"]["slot"],
                                        }
                                    )
                                if (
                                    "tarif" in slots
                                    and "slot" in slots["tarif"]
                                ):
                                    data[l["timestamp"]].update(
                                        {
                                            "Tarifa": slots["tarif"]["slot"],
                                        }
                                    )

                            dmc = lkp[1]
                            blk_pwr = _get_block_dogovorjena_moc(
                                data[l["timestamp"]], dmc
                            )
                            if blk_pwr is not None:
                                data[l["timestamp"]].update(
                                    {"Dogovorjena moč": float(blk_pwr)}
                                )

                            data[l["timestamp"]].update(
                                {lkp[0]: float(l["value"])}
                            )
                            data[l["timestamp"]].update(
                                {"obracunskaMoc": float(lkp[3])}
                            )
                    yield list(data.values())
                else:
                    raise StopAsyncIteration()

        else:
            raise StopAsyncIteration()

    async def lookup_slots(self, row: dict):
        slots = self.__time_blocks.get_time_slots(row)
        return slots

    async def __call__(
        self, session: ClientSession, params: dict | None = None
    ) -> dict | list | None:
        return await super().__call__(session, params)

    async def _process_return(self, resp: ClientResponse) -> dict | list | None:
        data = None
        if resp.status in [400, 401, 403]:
            try:
                errors = await resp.json()
                msg = None
                for error in errors["errors"]:
                    if msg is None:
                        msg = "Accessing meter_readings errore returned were:"
                    msg = msg + "{koda} - {opis}".format(**error)
                if msg is not None:
                    raise Exception(msg)
            except Exception as e:
                self._logger.error(
                    "Processing status {0} is not in defined form. Error: {1} ".format(
                        resp.status, repr(e)
                    )
                )
                resp.raise_for_status()
        else:
            data = await super()._process_return(resp)
        return data
