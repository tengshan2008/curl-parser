from parser import Parser
from typing import Any, Dict

import pywebio.input as webin
import pywebio.output as webout
import tornado.ioloop
import tornado.options
import tornado.web
from pywebio.platform.tornado import webio_handler


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")


def get_value(data: Dict[str, Any], key: str):
    if key not in data:
        return None
    
    if len(data[key]) == 0:
        return None

    return data[key]


def main():
    data = webin.input_group("接口信息", [
        webin.input("接口名称（中文）", name='title', type=webin.TEXT,
                    placeholder='title', required=True),
        webin.input("接口名称（英文）", name='name', type=webin.TEXT,
                    placeholder='apiName', required=True),
        webin.input("组名称", name='group', type=webin.TEXT,
                    placeholder='groupName', required=True),
        webin.input("版本号", name='version', type=webin.TEXT,
                    placeholder='0.0.1', required=False),
        webin.textarea("curl 命令", name='command', rows=10, required=True),
        webin.textarea("响应数据", name='response', rows=10),
    ])
    command = get_value(data, 'command')
    response = get_value(data, 'response')
    group = get_value(data, 'group')
    name = get_value(data, 'name')
    version = get_value(data, 'version')
    parser = Parser(command, response)
    doc = parser.to_apidoc(group=group, name=name, version=version)
    webout.put_text(doc)


# start_server(main, port=8080, debug=True)
application = tornado.web.Application([
    (r"/info", MainHandler),
    (r"/", webio_handler(main)),
])

if __name__ == "__main__":
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(5050)
    tornado.ioloop.IOLoop.current().start()
