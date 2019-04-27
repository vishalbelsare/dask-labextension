"""
A Dashboard handler for the Dask labextension.
This proxies the bokeh server http and ws requests through the notebook
server, preventing CORS issues.

Modified from the nbserverproxy project.
"""
from urllib import parse

from tornado import web

from notebook.utils import url_path_join
from jupyter_server_proxy.handlers import LocalProxyHandler

from .manager import manager


class DaskDashboardHandler(LocalProxyHandler):
    async def http_get(self, cluster_id, proxied_path):
        return await self.proxy(cluster_id, proxied_path)

    async def open(self, cluster_id, proxied_path):
        port = self._get_port(cluster_id)
        return await super().open(port, proxied_path)

    # We have to duplicate all these for now, I've no idea why!
    # Figure out a way to not do that?
    def post(self, cluster_id, proxied_path):
        return self.proxy(cluster_id, proxied_path)

    def put(self, cluster_id, proxied_path):
        return self.proxy(cluster_id, proxied_path)

    def delete(self, cluster_id, proxied_path):
        return self.proxy(cluster_id, proxied_path)

    def head(self, cluster_id, proxied_path):
        return self.proxy(cluster_id, proxied_path)

    def patch(self, cluster_id, proxied_path):
        return self.proxy(cluster_id, proxied_path)

    def options(self, cluster_id, proxied_path):
        return self.proxy(cluster_id, proxied_path)

    def proxy(self, cluster_id, proxied_path):
        port = self._get_port(cluster_id)
        return super().proxy(port, proxied_path)

    def _get_port(self, cluster_id):
        # Get the cluster by ID. If it is not found,
        # raise an error.
        cluster_model = manager.get_cluster(cluster_id)
        if not cluster_model:
            raise web.HTTPError(404, f"Dask cluster {cluster_id} not found")

        # Construct the proper websocket proxy link from the cluster dashboard
        dashboard_link = cluster_model["dashboard_link"]
        dashboard_link = _normalize_dashboard_link(dashboard_link, self.request)
        return parse.urlparse(dashboard_link).port or 443


def _normalize_dashboard_link(link, request):
    """
    Given a dashboard link, make sure it conforms to what we expect.
    """
    if not link.startswith('http'):
        # If a local url is given, assume it is using the same host
        # as the application, and prepend that.
        link = url_path_join(f"{request.protocol}://{request.host}", link)
    if link.endswith("/status"):
        # If the default "status" dashboard is give, strip it.
        link = link[:-len("/status")]
    return link
