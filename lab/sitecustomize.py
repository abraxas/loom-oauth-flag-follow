"""Install the lab harness before uvicorn imports Loom."""

import lab_patch

lab_patch.install_import_hook()
try:
    lab_patch.install()
except Exception:
    pass
