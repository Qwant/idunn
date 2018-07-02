from apistar import http

class CORSHeaders:
    def on_response(self, response: http.Response):
        response.headers['Access-Control-Allow-Origin'] = '*'
