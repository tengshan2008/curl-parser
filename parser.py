import argparse
import json
import warnings
from http.cookies import SimpleCookie
from shlex import split
from urllib.parse import urlparse

from w3lib.http import basic_auth_header


class CURLParser(argparse.ArgumentParser):
    def error(self, messasge):
        error_msg = f'There was an error parsing the curl command: {messasge}'
        raise ValueError(error_msg)

class BodyParser:
    def __init__(self, body) -> None:
        self.parse_body = {}
        self.parse(body)

    def insert_data(self, keys, value_type):
        keys_name = '.'.join(keys)
        if keys_name not in self.parse_body:
            self.parse_body[keys_name] = value_type


    def parse(self, body, keys=None):
        if keys is None:
            keys = []
        if isinstance(body, dict):
            for k, v in body.items():
                self.insert_data(keys + [k], v)
                self.parse(v, keys + [k])
        elif isinstance(body, list):
            for i in body:
                self.insert_data(keys, i)
                self.parse(i, keys)
        else:
            self.insert_data(keys, body)
        # elif isinstance(body, str):
        #     self.insert_data(keys, 'str')
        # elif isinstance(body, int):
        #     self.insert_data(keys, 'int')
        # elif isinstance(body, float):
        #     self.insert_data(keys, 'float')
        # elif isinstance(body, bool):
        #     self.insert_data(keys, 'bool')
        # else:
        #     self.insert_data(keys, 'unkown')


class Parser:
    def __init__(self, command: str) -> None:
        self.command = command.replace('\\\n', '').strip()
        self.curl_parser = self.init_parser()
        self.parsed = self.curl_to_request_kwargs()

    def init_parser(self) -> CURLParser:
        curl_parser = CURLParser()
        curl_parser.add_argument('url')
        curl_parser.add_argument(
            '-H', '--header', dest='headers', action='append')
        curl_parser.add_argument(
            '-X', '--request', dest='method', default='get')
        curl_parser.add_argument('-d', '--data-raw', dest='data')
        curl_parser.add_argument('-u', '--user', dest='auth')
        return curl_parser

    def curl_to_request_kwargs(self, ignore_unkown_options=True):
        curl_args = split(self.command)
        if curl_args[0] != 'curl':
            raise ValueError('A curl command must start with "curl"')

        parsed_args, argv = self.curl_parser.parse_known_args(curl_args[1:])
        if argv:
            msg = f'Unrecognized options: {", ".join(argv)}'
            if ignore_unkown_options:
                warnings.warn(msg)
            else:
                raise ValueError(msg)

        url = parsed_args.url
        parsed_url = urlparse(url)
        # print(parsed_url, "parsed_url---")

        if not parsed_url.scheme:
            url = 'http://' + url

        result = {'method': parsed_args.method.upper(), 'url': url,
                  'path': parsed_url.path, 'query': parsed_url.query}
        headers = []
        cookies = {}
        for header in parsed_args.headers or ():
            name, val = header.split(':', 1)
            name = name.strip()
            val = val.strip()
            if name.title() == 'Cookie':
                for name, morsel in SimpleCookie(val).items():
                    cookies[name] = morsel.value
            else:
                headers.append((name, val))

        if parsed_args.auth:
            user, password = parsed_args.auth.split(':', 1)
            headers.append(
                ('Authorization', basic_auth_header(user, password)))
        if headers:
            result['headers'] = headers
        if cookies:
            result['cookies'] = cookies
        if parsed_args.data:
            result['body'] = parsed_args.data
        return result

    def to_api(self):
        # @api {method} path title
        return f"@api {{{self.parsed['method']}}} {self.parsed['path']} title"

    def to_api_body(self):
        # @apiBody [{type}] [field=defaultValue] [description]
        lines = []
        body = json.loads(self.parsed['body'].strip())
        bp = BodyParser(body)
        for k, v in bp.parse_body.items():
            if isinstance(v, dict):
                ptype = 'Object'
            elif isinstance(v, list):
                ptype = 'List'
            elif isinstance(v, str):
                ptype = 'String'
            elif isinstance(v, int):
                ptype = 'Number'
            elif isinstance(v, bool):
                ptype = 'Bool'
            else:
                ptype = 'type'
            lines.append(f'@apiBody {{{ptype}}} {k} description')
        return '\n'.join(lines)

    def to_api_example(self):
        return f'@apiExample {{curl}} Example usage:{self.command}'

    def to_api_group(self, group: str = None):
        return f'@apiGroup {group}' if group else '@apiGroup group'

    def to_api_name(self, name: str = None):
        return f'@apiName {name}' if name else '@apiName apiName'

    def to_api_version(self, version: str = None):
        return f'@apiVersion {version}' if version else '@apiVersion 0.0.1'

    def to_api_header(self):
        # @apiHeader [(group)] [{type}] [field=defaultValue] [description]
        lines = []
        example = {}
        for header in self.parsed['headers']:
            if isinstance(header[1], str):
                ptype = 'String'
            elif isinstance(header[1], int):
                ptype = 'Number'
            else:
                ptype = 'type'
            lines.append(f'@apiHeader {{{ptype}}} {header[0]} description')
            example[header[0]] = header[1]
        example_text = json.dumps(example, indent='    ')

        header_example = f'@apiHeaderExample {{json}} Request-Example\n{example_text}'
        return '\n'.join(lines), header_example

    def to_api_query_param(self):
        # @apiParam {String} paramName description
        lines = []
        example = {}

        for query in self.parsed['query'].split('&'):
            if len(query) == 0:
                continue
            key, value = query.split('=')
            if isinstance(value, str):
                ptype = 'String'
            elif isinstance(value, int):
                ptype = 'Number'
            else:
                ptype = 'type'
            lines.append(f'@apiParam (query) {{{ptype}}} {key} description')
            example[key] = value

        if len(lines) == 0 or len(example) == 0:
            return "", ""

        example_text = json.dumps(example, indent='    ')
        param_example = f'@apiParamExample (query) {{json}} Request-Example:\n{example_text}'
        return "\n".join(lines), param_example

    def to_api_route_param(self):
        lines = []
        example = {}
        for pair in self.parsed['path'].split('/'):
            if pair.startswith(':'):
                lines.append(
                    f'@apiParam (route) {{String}} {pair[1:]} description')
                example[pair[1:]] = ""
        example_text = json.dumps(example, indent='    ')
        param_example = f'@apiParamExample (route) {{json}} Request-Example:\n{example_text}'
        return "\n".join(lines), param_example

    def to_api_success(self, response: str = None):
        # response = response.strip()
        # body = json.loads(response)
        # bp = BodyParser(json.loads(response))
        # for k, v in json.loads(response).items():
        #     pass
        success_example = f'@apiSuccessExample {{json}} Success-Response:\n{response}'
        return "", success_example

    def to_apidoc(
        self,
        group: str = None,
        name: str = None,
        version: str = '0.0.1',
        response: str = None,
    ):
        header, header_example = self.to_api_header()
        query_param, query_param_example = self.to_api_query_param()
        route_param, route_param_example = self.to_api_route_param()
        success, success_example = self.to_api_success(response)
        elements = [
            self.to_api(),
            self.to_api_name(name),
            self.to_api_group(group),
            self.to_api_version(version),
            self.to_api_example(),
            header,
            query_param,
            route_param,
            self.to_api_body(),
            success,
            header_example,
            query_param_example,
            route_param_example,
            success_example,
        ]
        elements = list(filter(lambda x: x and x.strip(), elements))
        body = '\n\n'.join(elements)
        return f'"""\n{body}\n"""'
