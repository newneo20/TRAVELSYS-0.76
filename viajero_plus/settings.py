# viajero_plus/settings.py
import os

_stage = (os.getenv("STAGE") or os.getenv("DJANGO_ENV") or "dev").lower()
USE_PROD = _stage == "prod"   # sólo STAGE/DJANGO_ENV deciden

if USE_PROD:
    from .envs.settings_prod import *  # noqa
else:
    from .envs.settings_dev import *   # noqa