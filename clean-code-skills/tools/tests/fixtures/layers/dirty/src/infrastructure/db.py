"""Repository that calls back into the domain - this closes the cycle."""
from ..domain.order import total  # inward, allowed on its own
from ..interface.routes import build_response  # outward: infra -> interface


class OrdersTable:
    pass
