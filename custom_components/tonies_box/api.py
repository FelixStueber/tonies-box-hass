import asyncio
import logging
import os
import socket
import time
import aiohttp
import async_timeout

_LOGGER = logging.getLogger(__name__)

API_BASE_URL = "https://api.tonie.cloud/v2"
GRAPHQL_URL = "https://api.prod.tcs.toys/v2/graphql"


class TonieboxApiClientError(Exception):
    """Exception to indicate a general API error."""


class TonieboxApiClientCommunicationError(TonieboxApiClientError):
    """Exception to indicate a communication error."""


class TonieboxApiClientAuthenticationError(TonieboxApiClientError):
    """Exception to indicate an authentication error."""


class TonieboxApiClient:
    def __init__(self, username, password, session: aiohttp.ClientSession) -> None:
        self._username = username
        self._password = password
        self._session = session
        self._token = None
        self._token_acquired_at: float = 0.0

    async def async_get_access_token(self) -> str:
        if self._token and (time.monotonic() - self._token_acquired_at) < 240:
            return self._token

        self._token = None  # clear stale token before re-auth

        payload = {
            "grant_type": "password",
            "client_id": "my-tonies",
            "scope": "openid",
            "username": self._username,
            "password": self._password,
        }

        try:
            async with async_timeout.timeout(10):
                async with self._session.post(
                    "https://login.tonies.com/auth/realms/tonies/protocol/openid-connect/token",
                    data=payload,
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    self._token = data.get("access_token")
                    if self._token is None:
                        raise TonieboxApiClientAuthenticationError(
                            "Access token not found in response"
                        )
                    self._token_acquired_at = time.monotonic()
                    return self._token
        except (asyncio.TimeoutError, aiohttp.ClientError) as exception:
            raise TonieboxApiClientAuthenticationError(
                "Error fetching token"
            ) from exception

    async def async_get_data(self):
        """Get all data from the API."""
        token = await self.async_get_access_token()
        headers = {"Authorization": f"Bearer {token}"}

        try:
            async with async_timeout.timeout(20):
                # Get Households
                async with self._session.get(
                    f"{API_BASE_URL}/households", headers=headers
                ) as resp:
                    if resp.status == 401:
                        self._token = None
                        self._token_acquired_at = 0.0
                        token = await self.async_get_access_token()
                        headers = {"Authorization": f"Bearer {token}"}
                        async with self._session.get(
                            f"{API_BASE_URL}/households", headers=headers
                        ) as resp2:
                            if resp2.status == 401:
                                raise TonieboxApiClientAuthenticationError(
                                    "Token refresh did not resolve 401"
                                )
                            resp2.raise_for_status()
                            households = await resp2.json()
                    else:
                        resp.raise_for_status()
                        households = await resp.json()

                data = {
                    "households": [],
                    "boxes": {},
                    "creative_tonies": {},
                    "tonies": {},
                }

                for household in households:
                    h_id = household["id"]
                    data["households"].append(household)

                    # Get Boxes
                    async with self._session.get(
                        f"{API_BASE_URL}/households/{h_id}/tonieboxes", headers=headers
                    ) as resp_boxes:
                        if resp_boxes.status == 200:
                            boxes = await resp_boxes.json()
                            for box in boxes:
                                box["household_id"] = h_id
                                data["boxes"][box["id"]] = box

                # Get All Tonies via GraphQL
                gql_query = {
                    "query": "query ContentTonies { households { id contentTonies { id title series { name } imageUrl } } }",
                    "operationName": "ContentTonies",
                    "variables": {},
                }
                async with self._session.post(
                    GRAPHQL_URL, json=gql_query, headers=headers
                ) as resp_gql:
                    if resp_gql.status == 200:
                        gql_data = await resp_gql.json()
                        if "data" in gql_data and "households" in gql_data["data"]:
                            for hh in gql_data["data"]["households"]:
                                h_id = hh["id"]
                                for tonie in hh.get("contentTonies", []):
                                    data["tonies"][tonie["id"]] = {
                                        "id": tonie["id"],
                                        "name": tonie["title"],
                                        "series": tonie.get("series", {}).get(
                                            "name", "Unknown"
                                        ),
                                        "imageUrl": tonie["imageUrl"],
                                        "household_id": h_id,
                                        "model": tonie.get("series", {}).get(
                                            "name", "Tonie Figurine"
                                        ),
                                    }
                            _LOGGER.debug(
                                "Fetched %s tonies via GraphQL", len(data["tonies"])
                            )
                    else:
                        _LOGGER.error(
                            "Failed to fetch tonies via GraphQL: %s", resp_gql.status
                        )

                # Get Creative Tonies via GraphQL
                gql_query_creative = {
                    "query": "query CreativeTonies { households { id creativeTonies { id name live private imageUrl secondsRemaining secondsPresent transcoding chapters { id title file seconds } } } }",
                    "variables": {},
                }
                async with self._session.post(
                    GRAPHQL_URL, json=gql_query_creative, headers=headers
                ) as resp_gql_creative:
                    if resp_gql_creative.status == 200:
                        gql_data = await resp_gql_creative.json()
                        if "data" in gql_data and "households" in gql_data["data"]:
                            for hh in gql_data["data"]["households"]:
                                h_id = hh["id"]
                                for tonie in hh.get("creativeTonies", []):
                                    tonie["household_id"] = h_id
                                    data["creative_tonies"][tonie["id"]] = tonie
                            _LOGGER.debug("Fetched creative tonies via GraphQL")
                    else:
                        _LOGGER.error(
                            "Failed to fetch creative tonies via GraphQL: %s",
                            resp_gql_creative.status,
                        )

                return data
        except (
            asyncio.TimeoutError,
            aiohttp.ClientError,
            socket.gaierror,
        ) as exception:
            raise TonieboxApiClientCommunicationError(
                "Error fetching data"
            ) from exception

    async def async_upload_file(self, tonie_id: str, file_path: str, title: str):
        """Upload a file to a Creative Tonie."""
        token = await self.async_get_access_token()
        headers = {"Authorization": f"Bearer {token}"}

        data = await self.async_get_data()
        if tonie_id not in data["creative_tonies"]:
            raise TonieboxApiClientError(f"Creative Tonie {tonie_id} not found")

        tonie_data = data["creative_tonies"][tonie_id]
        household_id = tonie_data["household_id"]
        current_chapters = tonie_data.get("chapters", [])

        filename = os.path.basename(file_path)
        async with self._session.post(
            f"{API_BASE_URL}/file", headers=headers, json={"filename": filename}
        ) as resp:
            resp.raise_for_status()
            upload_info = await resp.json()
            request_uuid = upload_info["requestUuid"]
            file_id = upload_info["fileId"]

        def read_file():
            with open(file_path, "rb") as f:
                return f.read()

        loop = asyncio.get_running_loop()
        file_content = await loop.run_in_executor(None, read_file)

        async with self._session.put(
            f"{API_BASE_URL}/file/{request_uuid}", headers=headers, data=file_content
        ) as resp:
            resp.raise_for_status()

        new_chapter = {"id": file_id, "file": file_id, "title": title, "seconds": 0}
        new_chapters = current_chapters + [new_chapter]

        async with self._session.patch(
            f"{API_BASE_URL}/households/{household_id}/creative_tonies/{tonie_id}",
            headers=headers,
            json={"chapters": new_chapters},
        ) as resp:
            resp.raise_for_status()

    async def async_add_chapter(self, tonie_id: str, file_id: str, title: str):
        """Add a chapter to a Creative Tonie using an existing file."""
        token = await self.async_get_access_token()
        headers = {"Authorization": f"Bearer {token}"}

        data = await self.async_get_data()
        if tonie_id not in data["creative_tonies"]:
            raise TonieboxApiClientError(f"Creative Tonie {tonie_id} not found")

        tonie_data = data["creative_tonies"][tonie_id]
        household_id = tonie_data["household_id"]
        current_chapters = tonie_data.get("chapters", [])

        new_chapter = {"id": file_id, "file": file_id, "title": title, "seconds": 0}
        new_chapters = current_chapters + [new_chapter]

        async with self._session.patch(
            f"{API_BASE_URL}/households/{household_id}/creative_tonies/{tonie_id}",
            headers=headers,
            json={"chapters": new_chapters},
        ) as resp:
            resp.raise_for_status()

    async def async_sort_chapters(self, tonie_id: str, chapters: list):
        """Sort chapters on a Creative Tonie."""
        token = await self.async_get_access_token()
        headers = {"Authorization": f"Bearer {token}"}

        data = await self.async_get_data()
        if tonie_id not in data["creative_tonies"]:
            raise TonieboxApiClientError(f"Creative Tonie {tonie_id} not found")

        tonie_data = data["creative_tonies"][tonie_id]
        household_id = tonie_data["household_id"]

        async with self._session.patch(
            f"{API_BASE_URL}/households/{household_id}/creative_tonies/{tonie_id}",
            headers=headers,
            json={"chapters": chapters},
        ) as resp:
            resp.raise_for_status()

    async def async_clear_chapters(self, tonie_id: str):
        """Clear all chapters from a Creative Tonie."""
        token = await self.async_get_access_token()
        headers = {"Authorization": f"Bearer {token}"}

        data = await self.async_get_data()
        if tonie_id not in data["creative_tonies"]:
            raise TonieboxApiClientError(f"Creative Tonie {tonie_id} not found")

        tonie_data = data["creative_tonies"][tonie_id]
        household_id = tonie_data["household_id"]

        async with self._session.patch(
            f"{API_BASE_URL}/households/{household_id}/creative_tonies/{tonie_id}",
            headers=headers,
            json={"chapters": []},
        ) as resp:
            resp.raise_for_status()

    async def async_set_volume(self, box_id: str, volume: int):
        """Set the maximum volume of a Toniebox."""
        data = await self.async_get_data()
        if box_id not in data["boxes"]:
            raise TonieboxApiClientError(f"Toniebox {box_id} not found")

        box_data = data["boxes"][box_id]
        household_id = box_data["household_id"]

        token = await self.async_get_access_token()
        headers = {"Authorization": f"Bearer {token}"}

        async with self._session.patch(
            f"{API_BASE_URL}/households/{household_id}/tonieboxes/{box_id}",
            headers=headers,
            json={"maxVolume": volume},
        ) as resp:
            resp.raise_for_status()

    async def async_set_led(self, box_id: str, led_level: str):
        """Set the LED status of a Toniebox."""
        data = await self.async_get_data()
        if box_id not in data["boxes"]:
            raise TonieboxApiClientError(f"Toniebox {box_id} not found")

        box_data = data["boxes"][box_id]
        household_id = box_data["household_id"]

        token = await self.async_get_access_token()
        headers = {"Authorization": f"Bearer {token}"}

        async with self._session.patch(
            f"{API_BASE_URL}/households/{household_id}/tonieboxes/{box_id}",
            headers=headers,
            json={"ledLevel": led_level},
        ) as resp:
            resp.raise_for_status()

    async def async_set_ear_slap(self, box_id: str, enabled: bool):
        """Set the ear slap status of a Toniebox."""
        data = await self.async_get_data()
        if box_id not in data["boxes"]:
            raise TonieboxApiClientError(f"Toniebox {box_id} not found")

        box_data = data["boxes"][box_id]
        household_id = box_data["household_id"]

        token = await self.async_get_access_token()
        headers = {"Authorization": f"Bearer {token}"}

        async with self._session.patch(
            f"{API_BASE_URL}/households/{household_id}/tonieboxes/{box_id}",
            headers=headers,
            json={"accelerometerEnabled": enabled},
        ) as resp:
            resp.raise_for_status()
