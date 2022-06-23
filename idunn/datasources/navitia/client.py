# TODO: use this
#  import httpx
#
#
#  class NavitiaClient:
#      def __init__(self):
#          self.session = httpx.AsyncClient(verify=settings["VERIFY_HTTPS"])
#          self.session.headers["User-Agent"] = settings["USER_AGENT"]
#
#      # TODO: some typing would be great
#      async def directions(self, start, end, mode, lang):
#          url = settings["NAVITIA_API_BASE_URL"]
#          params = {
#              "from": f"{start['lat']},{start['lon']}",
#              "to": f"{end['lat']},{end['lon']}",
#              "direct_path_mode[]": mode,
#          }
#
#          response = await self.session.get(url, params=params)
#          response.raise_for_status()
#          return response.json()
