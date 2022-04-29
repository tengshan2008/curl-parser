body = {
    'data': [
        {'name': '张山', 'gender': 0},
        {'name': '李氏', 'gender': 1}
    ],
    'message': '查询成功',
    'status': 200,
    'notice': ''
}

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


p = BodyParser(body)

print(p.parse_body)
# result = p.format_data()
# print(result)
