from logging import Logger

from moj_elektro_v1.http_access.http_JSON_conn import (
    ClientResponse,
    ClientSession,
    HTTPJSONConnection,
)

reading_type_mt_vrsta = {
    "delovna prejem": "OMTO",
    "delovna oddaja": "MTP",
    "jalova prejem": "OMTO",
    "jalova oddaja": "MTP",
    "delovna prejem ET": "OMTO",
    "delovna prejem VT": "OMTO",
    "delovna prejem MT": "OMTO",
    "delovna oddaja ET": "MTP",
    "delovna oddaja VT": "MTP",
    "delovna oddaja MT": "MTP",
    "jalova prejem ET": "OMTO",
    "jalova prejem VT": "OMTO",
    "jalova prejem MT": "OMTO",
    "jalova oddaja ET": "MTP",
    "jalova oddaja VT": "MTP",
    "jalova oddaja MT": "MTP",
}


class MeterType(HTTPJSONConnection):
    def __init__(self, api_key: str, logger: Logger | None = None) -> None:
        super().__init__(
            {
                "X-API-TOKEN": f"{api_key}",
                "accept": "application/json",
            },
            "https://api.informatika.si/mojelektro/v1/reading-type",
            logger,
        )

    @classmethod
    async def get_reading_type_lookup(
        cls,
        session: ClientSession,
        api_key: str,
        oznaka_list: list,
        mt_params: dict[str, tuple[list, int, int]],
        logger: Logger | None = None,
    ) -> dict[str, tuple[str, list, int, int]]:
        rts = cls(api_key, logger)
        reading_types = await rts(session)
        lookup_reading_list = {}
        if reading_types is not None and isinstance(reading_types, list):
            for reading_type in reading_types:
                if isinstance(reading_type, dict):
                    if (
                        "oznaka" in reading_type
                        and reading_type["oznaka"] in oznaka_list
                    ):
                        mt_vrsta = reading_type_mt_vrsta.get(
                            reading_type["tip"], "UNK"
                        )
                        params = mt_params.get(mt_vrsta, None)
                        if params is not None:
                            lookup_reading_list[reading_type["readingType"]] = (
                                reading_type["oznaka"],
                                params[0],
                                params[1],
                                params[2],
                            )
        return lookup_reading_list

    async def __call__(
        self, session: ClientSession, parameters: dict | None = None
    ) -> dict | list | None:
        return await super().__call__(session, None)

    async def _process_return(self, resp: ClientResponse) -> dict | list | None:
        data = None
        if resp.status in [401, 403]:
            try:
                errors = await resp.json()
                msg = None
                for error in errors["errors"]:
                    if msg is None:
                        msg = "Accessing meter_type errors returned were:"
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
