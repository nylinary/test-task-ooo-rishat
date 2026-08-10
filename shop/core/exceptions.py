class ApplicationError(Exception):
    """
    Base error for everything that is "expected" business-logic wise.

    Services and selectors raise it, the DRF exception handler
    (`shop.api.exception_handlers`) turns it into a 400 response and the
    server-rendered views turn it into a readable error page.
    """

    def __init__(self, message: str, extra: dict | None = None):
        super().__init__(message)

        self.message = message
        self.extra = extra or {}
