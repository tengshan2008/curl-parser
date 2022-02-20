from parser import Parser

curl_command = """

"""

parser = Parser(curl_command)
# print(parser.parsed)
doc = parser.to_apidoc()
print(doc)
