from parser import Parser
from pywebio import start_server
import pywebio.input as webin
import pywebio.output as webout


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
    parser = Parser(data['command'])
    doc = parser.to_apidoc(
        group=data['group'], name=data['name'], version=data['version'])
    webout.put_text(doc)


start_server(main, port=8080, debug=True)
