from logging import Logger

from moj_elektro_v1.http_access.http_JSON_conn import (
    ClientResponse,
    ClientSession,
    HTTPJSONConnection,
)
from moj_elektro_v1.web_api_access.merilno_mesto import MerilnoMesto


class MerilnaTocka(HTTPJSONConnection):
    def __init__(
        self, MT_GRSN: str, api_key: str, logger: Logger | None = None
    ) -> None:
        super().__init__(
            {
                "X-API-TOKEN": f"{api_key}",
                "accept": "application/json",
            },
            f"https://api.informatika.si/mojelektro/v1/merilna-tocka/{MT_GRSN}",
            logger,
        )

    @classmethod
    async def get_merilne_tocke(
        cls,
        session: ClientSession,
        api_key: str,
        EIMM: str,
        logger: Logger | None = None,
    ) -> list:
        tocke = []
        mm_data = await MerilnoMesto.get_merilno_mesto(
            session, api_key, EIMM, logger
        )
        if "merilneTocke" in mm_data:
            for mt in mm_data["merilneTocke"]:
                if "gsrn" in mt:
                    tocka = cls(mt["gsrn"], api_key)
                    t = await tocka(session)
                    tocke.append(t)
        return tocke

    @classmethod
    async def get_parameters_by_vrsta(
        cls,
        session: ClientSession,
        api_key: str,
        EIMM: str,
        logger: Logger | None = None,
    ) -> dict[str, tuple[list, int, int]]:
        params = {}
        mt_list = await cls.get_merilne_tocke(session, api_key, EIMM, logger)
        for mt in mt_list:
            params[mt["vrsta"]] = (
                mt["dogovorjeneMoci"],
                mt["steviloTarifMerjenja"],
                mt["obracunskaMoc"],
            )
        return params

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
                        msg = "Accessing merilna_tocka errors returned were:"
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
