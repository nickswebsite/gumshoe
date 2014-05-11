import traceback

class ExceptionLoggerMiddleware(object):
    def process_exception(self, request, exception):
        print(exception)
        print(traceback.format_exc())
