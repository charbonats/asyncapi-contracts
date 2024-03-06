from .my_app import app

# It is recommended to only export the app instance from the contract module.
# Endpoints should be imported from their respective modules.
# If you want to know what are all endpoints available, endpoints should
# be all listed in `my_app.py` anyway
__all__ = ["app"]
