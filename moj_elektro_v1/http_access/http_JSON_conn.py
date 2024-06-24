from logging import Logger, getLogger

from aiohttp import ClientResponse, ClientSession


class HTTPJSONConnection(object):
    def __init__(
        self, header: dict, url: str, logger: Logger | None = None
    ) -> None:
        self._logger = (
            logger
            if logger is not None
            else getLogger("HTTPJSONConnectionLogger")
        )
        self._url = url
        self._header = header

    @classmethod
    def get_session(cls):
        return ClientSession()

    async def __call__(
        self, session: ClientSession, parameters: dict | None = None
    ) -> dict | list | None:
        data = None
        self._logger.info("Accessing: {0}".format(self._url))
        if parameters is None:
            async with session.get(self._url, headers=self._header) as resp:
                data = await self._process_return(resp)
        else:
            self._logger.info("Parameters: {0}".format(parameters))
            async with session.get(
                self._url, headers=self._header, params=parameters
            ) as resp:
                data = await self._process_return(resp)
        return data

    async def _process_return(self, resp: ClientResponse):
        data = None
        if resp.status == 200:
            try:
                data = await resp.json()
            except Exception as e:
                raise Exception("JSON was not in proper format: {0}".format(e))
        else:
            resp.raise_for_status()
        return data
