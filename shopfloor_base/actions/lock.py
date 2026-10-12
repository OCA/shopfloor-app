# Copyright 2022 Michael Tietz (MT Software) <mtietz@mt-software.de>
# Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import hashlib
import logging
import struct
import time
from functools import partial

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

        The lock mode is 'FOR NO KEY UPDATE', as used by Odoo core in similar
        situations. It avoids blocking concurrent inserts referencing the locked rows
        through a foreign key.
        """
        query = "SELECT id FROM %s WHERE ID IN %%s FOR NO KEY UPDATE"
        if skip_locked:
            query += " SKIP LOCKED"
        sql = query % records._table

        if _logger.isEnabledFor(logging.DEBUG):
            _logger.debug(
                "Trying to acquire lock on %s for IDs %s%s",
                records._table,
                sorted(records.ids),
                " with SKIP LOCKED" if skip_locked else "",
            )
            start_time = time.perf_counter()

        self.env.cr.execute(sql, (tuple(records.ids),), log_exceptions=log_exceptions)

        rows = self.env.cr.fetchall()

        if _logger.isEnabledFor(logging.DEBUG):
            _logger.debug(
                "Lock was acquired on %s for IDs %s in %.4f seconds",
                records._table,
                sorted(row[0] for row in rows),
                time.perf_counter() - start_time,
            )
            # NOTE: if the lock was acquired inside a savepoint that is later
            # rolled back, PostgreSQL releases it right away, while the
            # "released" log below is emitted only on full transaction
            # rollback or commit. The log can therefore be late or missing.
            self.env.cr.postcommit.add(partial(self._log_lock_release, records))
            self.env.cr.postrollback.add(partial(self._log_lock_release, records))

        if skip_locked:
            return len(rows) == len(records)
        return True

    def _log_lock_release(self, records):
        _logger.debug(
            "Lock was released on %s for IDs %s",
            records._table,
            sorted(records.ids),
        )
