from apistar import App

class IdunnApp(App):
    def __call__(self, environ, start_response):
        def get_default_state():
            return {
                'environ': environ,
                'start_response': start_response,
                'exc': None,
                'app': self,
                'path_params': None,
                'route': None,
                'response': None,
            }

        state = get_default_state()
        method = environ['REQUEST_METHOD'].upper()
        path = environ['PATH_INFO']

        if self.event_hooks is None:
            on_request, on_response, on_error = [], [], []
        else:
            on_request, on_response, on_error = self.get_event_hooks()

        try:
            route, path_params = self.router.lookup(path, method)
            state['route'] = route
            state['path_params'] = path_params
            if route.standalone:
                funcs = [route.handler]
            else:
                funcs = (
                    on_request +
                    [route.handler, self.render_response] +
                    on_response +
                    [self.finalize_wsgi]
                )
            return self.injector.run(funcs, state)
        except Exception as exc:
            # This is the only change with the parent class.
            # The `state` that caused the exception is not reused
            # to avoid polluting the injector cache
            # with partial dependency resolution.
            exc_state = get_default_state()
            exc_state['exc'] = exc
            if 'route' in state:
                exc_state['route'] = state['route']
            if 'path_params' in state:
                exc_state['path_params'] = state['path_params']
            return self.handle_request_exception(exc_state, on_response, on_error)

    def handle_request_exception(self, state, on_response, on_error):
        try:
            funcs = (
                [self.exception_handler] +
                on_response +
                [self.finalize_wsgi]
            )
            return self.injector.run(funcs, state)
        except Exception as inner_exc:
            try:
                state['exc'] = inner_exc
                self.injector.run(on_error, state)
            finally:
                funcs = [self.error_handler, self.finalize_wsgi]
                return self.injector.run(funcs, state)
