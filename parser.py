import argparse
import json
import warnings
from http.cookies import SimpleCookie
from shlex import split
from typing import Tuple
from urllib.parse import urlparse

from w3lib.http import basic_auth_header

API_QUERY_PARAM_EXAMPLE = "@apiParamExample (query) {json} Request-Example:"
API_ROUTE_PARAM_EXAMPLE = "@apiParamExample (route) {json} Request-Example:"
API_HEADER_EXAMPLE = "@apiHeaderExample {json} Request-Example"
API_SUCCESS_EXAMPLE = "@apiSuccessExample {json} Success-Response:"


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


class Parser:
    def __init__(self, command: str, response: str) -> None:
        self.command = command.replace('\\\n', '').strip()
        self.response = response.replace('\\\n', '').strip()
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

    def to_api(self, title: str = "title") -> str:
        # @api {method} path title
        method = self.parsed['method']
        path = self.parsed['path']
        return f"@api {{{method}}} {path} {title}"

    def to_api_body(self) -> str:
        # @apiBody [{type}] [field=defaultValue] [description]
        if 'body' not in self.parsed:
            return None
        body_text = self.parsed['body'].strip()

        lines = []

        body = json.loads(body_text)
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

    def to_api_example(self) -> str:
        # @apiExample [{type}] title
        #     example
        return f'@apiExample {{curl}} Example usage:\n{self.command}'

    def to_api_group(self, group: str) -> str:
        # @apiGroup name
        return f'@apiGroup {group}'

    def to_api_name(self, name) -> str:
        # @apiName name
        return f'@apiName {name}'

    def to_api_version(self, version) -> str:
        # @apiVersion version
        return f'@apiVersion {version}'

    def to_api_header(self) -> Tuple[str, str]:
        # @apiHeader [(group)] [{type}] [field=defaultValue] [description]
        if 'headers' not in self.parsed:
            return None
        headers = self.parsed['headers']

        lines = []
        example = {}

        for header in headers:
            header_name, header_value = header
            example[header_name] = header_value
            lines.append(f'@apiHeader {{String}} {header_name} description')

        header_lines = '\n'.join(lines)
        example_text = json.dumps(example, indent='    ', ensure_ascii=False)
        header_example = f'{API_HEADER_EXAMPLE}\n{example_text}'

        return header_lines, header_example

    def to_api_query_param(self) -> Tuple[str, str]:
        # @apiParam (query) {String} paramName description
        if 'query' not in self.parsed:
            return None, None
        query_string = self.parsed['query']

        lines = []
        example = {}

        for query in query_string.split('&'):
            if len(query) == 0:
                continue
            key, value = query.split('=')
            example[key] = value
            lines.append(f'@apiParam (query) {{String}} {key} description')

        if len(lines) == 0 or len(example) == 0:
            return None, None

        param_lines = '\n'.join(lines)
        example_text = json.dumps(example, indent='    ', ensure_ascii=False)
        param_example = f'{API_QUERY_PARAM_EXAMPLE}\n{example_text}'

        return param_lines, param_example

    def to_api_route_param(self) -> Tuple[str, str]:
        # @apiParam (route) {String} paramName description
        if 'path' not in self.parsed:
            return None, None
        path_string = self.parsed['path']

        lines = []
        example = {}

        for param in path_string.split('/'):
            if param.startswith(':'):
                param_name = param[1:]
                example[param_name] = param_name
                lines.append(
                    f'@apiParam (route) {{String}} {param_name} description')

        if len(lines) == 0 or len(example) == 0:
            return None, None

        param_lines = '\n'.join(lines)
        example_text = json.dumps(example, indent='    ', ensure_ascii=False)
        param_example = f'{API_ROUTE_PARAM_EXAMPLE}\n{example_text}'

        return param_lines, param_example

    def to_api_success(self) -> Tuple[str, str]:
        # @apiSuccess [(group)] [{type}] field [description]
        if self.response is None:
            return None, None

        lines = []

        success = json.loads(self.response)
        bp = BodyParser(success)
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
            lines.append(f'@apiSuccess {{{ptype}}} {k} description')

        success_lines = '\n'.join(lines)
        success_text = json.dumps(success, indent='    ', ensure_ascii=False)
        success_example = f'{API_SUCCESS_EXAMPLE}\n{success_text}'

        return success_lines, success_example

    def to_apidoc(
        self,
        group: str = "group",
        name: str = "name",
        version: str = '0.0.1',
    ):
        header, header_example = self.to_api_header()
        query_param, query_param_example = self.to_api_query_param()
        route_param, route_param_example = self.to_api_route_param()
        success, success_example = self.to_api_success()
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
