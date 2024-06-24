from logging import Logger

from moj_elektro_v1.http_access.http_JSON_conn import (
    ClientResponse,
    ClientSession,
    HTTPJSONConnection,
)


class MerilnoMesto(HTTPJSONConnection):
    def __init__(
        self, EIMM: str, api_key: str, logger: Logger | None = None
    ) -> None:
        super().__init__(
            {
                "X-API-TOKEN": f"{api_key}",
                "accept": "application/json",
            },
            f"https://api.informatika.si/mojelektro/v1/merilno-mesto/{EIMM}",
            logger,
        )

    @classmethod
    async def get_merilno_mesto(
        cls,
        session: ClientSession,
        api_key: str,
        EIMM: str,
        logger: Logger | None = None,
    ):
        mm = MerilnoMesto(EIMM, api_key, logger)
        mm_data = await mm(session)

        return mm_data

    async def __call__(
        self, session: ClientSession, parameters: dict | None = None
    ) -> dict | list | None:
        return await super().__call__(session, None)

    async def _process_return(self, resp: ClientResponse) -> dict | list | None:
        data = None
        if resp.status in [400, 401, 403, 404]:
            try:
                errors = await resp.json()
                msg = None
                for error in errors["errors"]:
                    if msg is None:
                        msg = "Accessing merilno_mesto errors returned were:"
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
