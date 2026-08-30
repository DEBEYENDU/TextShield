"""Repository package: one module per aggregate, thin SQL access.

Repositories take an active connection from ``app.database.base``
(``get_connection`` / ``get_read_connection``) so callers control the
transaction scope. All row access is parameterized; no dynamic SQL.
"""

from __future__ import annotations
