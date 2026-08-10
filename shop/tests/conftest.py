import pytest


@pytest.fixture(autouse=True)
def _plain_staticfiles_storage(settings):
    """
    The manifest storage used in production requires `collectstatic` to have
    run - irrelevant for tests, so fall back to the plain storage.
    """
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
