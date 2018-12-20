from werkzeug.routing import BaseConverter


class ReConverter(BaseConverter):
    """自定义正则表达式路由"""
    def __init__(self, url_map, regex):
        super(ReConverter, self).__init__(url_map)
        self.regex = regex
