import requests
from typing import Optional, Any
from .session import TonieCloudSession


class ToniesAPIError(Exception):
    """Raised when the Tonies API returns an error."""
    pass


class ToniesClient:
    BASE_URL = "https://api.tonie.cloud/v2/graphql"

    def __init__(self,  username: str, password: str, timeout: int = 30):
        """Initializes the API and creates a session token for tonie cloud session."""
        self.session = TonieCloudSession()
        self.session.acquire_token(username=username, password=password, timeout=timeout)
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.session.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def execute(
        self,
        query: str,
        variables: Optional[dict[str, Any]] = None,
        operation_name: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Execute a GraphQL query or mutation.
        """
        payload: dict[str, Any] = {"query": query}

        if variables is not None:
            payload["variables"] = variables

        if operation_name:
            payload["operationName"] = operation_name

        response = requests.post(
            self.BASE_URL,
            json=payload,
            headers=self._headers(),
            timeout=self.timeout,
        )

        if not response.ok:
            raise ToniesAPIError(
                f"HTTP {response.status_code}: {response.text}"
            )

        data = response.json()

        if "errors" in data:
            raise ToniesAPIError(data["errors"])

        return data.get("data", {})

    # =========================
    # High-level API methods
    # =========================

    def get_me(self) -> dict[str, Any]:
        """
        Returns the currently authenticated user.
        """
        query = """
        query Me {
          me {
            id
            email
            firstName
            lastName
          }
        }
        """
        return self.execute(query)["me"]

    def get_households(self) -> list[dict[str, Any]]:
        """
        Returns all households for the current account.
        """
        query = """
        query Households {
          households {
            id
            name
          }
        }
        """
        return self.execute(query)["households"]

    def list_tonieboxes(self) -> list[dict[str, Any]]:
        """
        Returns all Toniebox devices linked to the account.
        """
        query = """
        query Devices {
          devices {
            id
            name
            serialNumber
            online
          }
        }
        """
        return self.execute(query)["devices"]

    def list_creative_tonies(self) -> list[dict[str, Any]]:
        """
        Returns all Creative Tonies in the library.
        """
        query = """
        query CreativeTonies {
          creativeTonies {
            id
            title
            description
            duration
          }
        }
        """
        return self.execute(query)["creativeTonies"]

    def get_all_creative_tonies_by_household(
        self, household_id: str
    ) -> list[dict]:
        """
        Returns all Creative Tonies for a given household.
        """
        query = """
        {
          households {
            access
            canLeave
            foreignCreativeTonieContent
            id
            image
            name
            ownerName
            creativeTonies {
              id
              name
              live
              private
              imageUrl
              secondsRemaining
              secondsPresent
              tune {
                item {
                  title
                  languageUnicode
                  __typename
                }
                __typename
              }
              _typename
            }
            __typename
          }
          contentTokens(first: 12, selection: "public", region: "geoip") {
            edges {
              node {
                token
                title
                subtitle
                thumbnail
                __typename
              }
              __typename
            }
            __typename
          }
        }
        """

        variables = {"householdId": household_id}

        result = self.execute(query, variables)

        household = result.get("household")
        if not household:
            return []

        return household.get("creativeTonies", [])
    
    def get_tonieboxes(self) -> list[dict]:
        """
        Returns all Tonieboxes across all households.
        """
        query = """
        query {
          households {
            id
            name
            tonieboxes {
              id
              name
              imageUrl
              householdId
            }
          }
        }
        """

        result = self.execute(query)

        tonieboxes: list[dict] = []

        for household in result.get("households", []):
            for box in household.get("tonieboxes", []):
                box["householdName"] = household.get("name")
                tonieboxes.append(box)

        return tonieboxes