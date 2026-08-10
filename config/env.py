from pathlib import Path

import environ

env = environ.Env()


def read_env_file(base_dir: Path) -> None:
    """
    Load a local `.env` file, if present.

    In production (Docker / Railway) the environment is populated by the
    platform, so the file is simply absent and everything comes from the
    real environment.
    """
    env_file = base_dir / ".env"

    if env_file.exists():
        env.read_env(str(env_file))
