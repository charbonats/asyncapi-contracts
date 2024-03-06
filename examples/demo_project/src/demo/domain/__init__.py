from .my_endpoint import MyEndpoint

# It is recommended to export endpoints from the domain module
# in a single location. This makes it easier to import them
# from the infra module and make it easy to see what is available.
__all__ = ["MyEndpoint"]
