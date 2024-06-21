from logging import Logger

from moj_elektro_v1.http_access.http_JSON_conn import (
    ClientSession,
    HTTPJSONConnection,
)


class MeterQualities(HTTPJSONConnection):
    def __init__(self, api_key: str, logger: Logger | None = None) -> None:
        super().__init__(
            {
                "X-API-TOKEN": f"{api_key}",
                "accept": "application/json",
            },
            "https://api.informatika.si/mojelektro/v1/reading-qualities",
            logger,
        )

    async def __call__(
        self, session: ClientSession, parameters: dict | None = None
    ) -> dict | list | None:
        return await super().__call__(session, None)

    async def _process_return(self, resp) -> dict | list | None:
        data = None
        if resp.status in [401, 403]:
            errors = await resp.json()
            msg = None
            for error in errors["errors"]:
                if msg is None:
                    msg = "Accessing meter_qualities the errors returned was:"
                msg = msg + "{koda} - {opis}".format(**error)
            if msg is not None:
                raise Exception(msg)

        else:
            data = await super()._process_return(resp)
        return data
