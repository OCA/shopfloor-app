# Copyright 2022 Michael Tietz (MT Software) <mtietz@mt-software.de>
# Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import hashlib
import logging
import struct
import time
from functools import partial

from odoo.tools import str2bool

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class LockAction(Component):
    """Provide methods to create database locks"""

    _name = "shopfloor.lock.action"
    _inherit = "shopfloor.process.action"
    _usage = "lock"

    def advisory(self, name):
        """
        Create a blocking advisory lock
        The lock is released at the commit or rollback of the transaction.
        """
        hasher = hashlib.sha1(str(name).encode())
        # pg_lock accepts an int8 so we build an hash composed with
        # contextual information and we throw away some bits
        int_lock = struct.unpack("q", hasher.digest()[:8])

        self.env.cr.execute("SELECT pg_advisory_xact_lock(%s);", (int_lock,))
        self.env.cr.fetchone()[0]

    def for_update(self, records, log_exceptions=False, skip_locked=False):
        """Lock rows for update on a specific table.

        This function will try to obtain a lock on the rows (records parameter) and
        wait until they are available for update.

        Using the SKIP LOCKED parameter (better used with only one record), it will
        not wait for the row to be available but return False if the lock could not
        be obtained.

        """
        no_key = str2bool(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("shopfloor.lock.for_update.no_key")
        )
        no_wait = str2bool(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("shopfloor.lock.for_update.no_wait")
        )

        for_update_str = " FOR NO KEY UPDATE " if no_key else " FOR UPDATE "
        query = "SELECT id FROM %s WHERE ID IN %%s " + for_update_str

        suffix = ""
        if skip_locked:
            suffix = " SKIP LOCKED"
        elif no_wait:
            suffix = " NOWAIT"
        query += suffix

        sql = query % records._table

        with_suffix_str = f" with suffix{suffix}" if suffix else ""
        _logger.debug(
            f"Trying to acquire {for_update_str} lock{with_suffix_str} on "
            f"{records._table} for IDs {sorted(records.ids)}"
        )

        start_time = time.perf_counter()

        self.env.cr.execute(sql, (tuple(records.ids),), log_exceptions=log_exceptions)

        end_time = time.perf_counter()
        execute_time = end_time - start_time

        rows = self.env.cr.fetchall()
        _logger.debug(
            f"Lock was acquired on {records._table} for IDs "
            f"{sorted([row[0] for row in rows])} in {execute_time:0.4f} seconds"
        )

        self.env.cr.postcommit.add(partial(self._log_lock_release, records))
        self.env.cr.postrollback.add(partial(self._log_lock_release, records))

        if skip_locked:
            return len(rows) == len(records)
        return True

    def _log_lock_release(self, records):
        _logger.debug(
            f"Lock was released on {records._table} for IDs {sorted(records.ids)}"
        )
