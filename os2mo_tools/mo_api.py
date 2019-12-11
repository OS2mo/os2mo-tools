#
# Copyright (c) 2018, Magenta ApS
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
"""A simple API for requesting data from MO."""
import logging
from collections import defaultdict

import requests
from cached_property import cached_property

logger = logging.getLogger(__name__)


class MOData:
    """Abstract base class to interface with MO objects."""

    def __init__(self, uuid, connector):
        """Initialize object from ``uuid``."""
        self.uuid = uuid
        self.connector = connector
        self._stored_details = defaultdict(list)

    @cached_property
    def json(self):
        """JSON representation of the object itself (no details)."""
        return self.connector.mo_get(self.url)

    @cached_property
    def children(self):
        """Children of the current object.

        Will currently only work with Org Units.
        """
        return self.connector.mo_get(self.url + "/children")

    @cached_property
    def _details(self):
        return self.connector.mo_get(self.url + "/details/")

    def _get_detail(self, detail):
        return self.connector.mo_get(self.url + "/details/" + detail)

    def __getattr__(self, name):
        """Get details if field in details for object.

        Available details for OrgFunc are: address, association,
        engagement, it, leave, manager, org_unit, role
        """
        if name in self._details:
            if name not in self._stored_details and self._details[name]:
                self._stored_details[name] = self._get_detail(name)
            return self._stored_details[name]
        else:
            raise AttributeError("No such attribute: {}".format(name))

    def __str__(self):
        """String representation - JSON representation without details."""
        return str(self.json)


class OrgUnit(MOData):
    """A MO organisation unit, e.g. a department in a municipality."""

    def __init__(self, uuid, connector):
        """Initialize the org unit by specifying the URL prefix."""
        super().__init__(uuid, connector)
        self.url = connector.mo_url + "/ou/" + self.uuid


class Employee(MOData):
    """A MO employee."""

    def __init__(self, uuid, connector):
        """Initialize the employee by specifying the URL prefix."""
        super().__init__(uuid, connector)
        self.url = connector.mo_url + "/e/" + self.uuid


class Connector:
    def __init__(self, mo_url, org_uuid=None, api_token=None):
        self.mo_url = mo_url
        self.api_token = api_token
        self.session = requests.Session()
        if api_token:
            self.session.headers["session"] = api_token

        if org_uuid:
            self.org_id = org_uuid
        else:
            self.org_id = self._get_org()

    def mo_get(self, url):
        """Helper function for getting data from MO.

        Return JSON content if successful, throw exception if not.
        """
        result = self.session.get(url, verify=False)
        if not result:
            result.raise_for_status()
        else:
            return result.json()

    def _get_org(self):
        organisations = self.mo_get(self.mo_url + "/o/")
        if organisations:
            if len(organisations) > 1:
                logger.warning(
                    "More than one organisation exists in LoRa. Using first one found"
                )
            return organisations[0]["uuid"]

        raise Exception('No organisation found in LoRa')

    def get_ous(self):
        """Get all organization units belonging to org_id."""
        ou_url = self.mo_url + "/o/" + self.org_id + "/ou/"
        total_ous = self.mo_get("{}?limit=1".format(ou_url))["total"]
        offset = 1000
        start = 0

        while start < total_ous:
            yield from self.mo_get(
                "{}?limit={}&start={}".format(ou_url, offset, start)
            )["items"]
            start += offset

    def get_ou_connector(self, org_unit_uuid):
        return OrgUnit(org_unit_uuid, self)

    def get_employees(self):
        """Get all employees belonging to the given organization."""
        employee_url = self.mo_url + "/o/" + self.org_id + "/e/"
        total_employees = self.mo_get("{}?limit=1".format(employee_url))["total"]
        offset = 1000
        start = 0

        while start < total_employees:
            yield from self.mo_get(
                "{}?limit={}&start={}".format(employee_url, offset, start)
            )["items"]
            start += offset

    def get_employee_connector(self, employee_uuid):
        return Employee(employee_uuid, self)
