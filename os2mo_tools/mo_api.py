#
# Copyright (c) 2018, Magenta ApS
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
"""A simple API for requesting data from MO."""

import os
import functools

from collections import defaultdict

import requests

from cached_property import cached_property

global_session = requests.Session()


DEFAULT_MO_URL = os.environ.get(
        'MO_URL', 'http://morademo.atlas.magenta.dk/service'
)
ORG_ROOT = os.environ.get(
    'MO_ORG_ROOT', '293089ba-a1d7-4fff-a9d0-79bd8bab4e5b'
)


def mo_get(url, session=None):
    """Helper function for getting data from MO.

    Return JSON content if successful, throw exception if not.
    """
    result = session.get(url) if session else global_session.get(url)
    if not result:
        result.raise_for_status()
    else:
        return result.json()


class MOData:
    """Abstract base class to interface with MO objects."""

    def __init__(self, uuid):
        """Initialize object from ``uuid``."""
        self.uuid = uuid
        self._stored_details = defaultdict(list)
        self.session = global_session
        self.get = functools.partial(mo_get, session=self.session)

    @cached_property
    def json(self):
        """JSON representation of the object itself (no details)."""
        return self.get(self.url)

    @cached_property
    def children(self):
        """Children of the current object.

        Will currently only work with Org Units.
        """
        return self.get(self.url + '/children')

    @cached_property
    def _details(self):
        return self.get(self.url + '/details/')

    def _get_detail(self, detail):
        return self.get(self.url + '/details/' + detail)

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


class MOOrgUnit(MOData):
    """A MO organisation unit, e.g. a department in a municipality."""

    def __init__(self, uuid, mo_url=DEFAULT_MO_URL):
        """Initialize the org unit by specifying the URL prefix."""
        super().__init__(uuid)
        self.url = mo_url + '/ou/' + self.uuid


class MOEmployee(MOData):
    """A MO employee."""

    def __init__(self, uuid, mo_url=DEFAULT_MO_URL):
        """Initialize the employee by specifying the URL prefix."""
        super().__init__(uuid)
        self.url = mo_url + '/e/' + self.uuid


def get_ous(org_id=ORG_ROOT, mo_url=DEFAULT_MO_URL):
    """Get all organization units belonging to org_id."""
    return mo_get(mo_url + '/o/' + org_id + '/ou/')['items']


def get_employees(org_id=ORG_ROOT, mo_url=DEFAULT_MO_URL):
    """Get all employees belonging to the given organization."""
    return mo_get(mo_url + '/o/' + org_id + '/e/')['items']


if __name__ == '__main__':  # pragma: no cover
    # Note: This is just a quick smoke test. Will only work if
    # DEFAULT_MO_URL and ORG_ROOT are properly configured.
    ou_uuid = get_ous(ORG_ROOT)[0]['uuid']
    e_uuid = get_employees(ORG_ROOT)[0]['uuid']
    ou = MOOrgUnit(ou_uuid)
    e = MOEmployee(e_uuid)
    print(ou.json['name'])
    print(e.json['name'])
