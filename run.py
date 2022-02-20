from parser import Parser

curl_command = """
curl --location --request POST 'http://82.157.13.14:8088/api/v1/category/:category_id/standard_corpus/:standard_corpus_id?q=123&w=456' \
--header 'User-Agent: Apipost client Runtime/+https://www.apipost.cn/' \
--header 'Connection: keep-alive' \
--header 'Accept: application/json' \
--header 'DNT: 1' \
--header 'Authorization: eyJhbGciOiJIUzUxMiJ9.eyJ0ZW5hbnRfaWQiOjksInN1YiI6IuWQm-iPgeWunCIsImV4cCI6MTY0NTIzNTAzNywidXNlcklkIjo1LCJpYXQiOjE2NDUxNDg2Mzd9.7w1_TlospfqeHEHDSTtZfuEwLCch0jgnqtG1qOLDR8dzaR4aAg-tIfH8J61L-0fq8FjMpbp26gkda8--KBkRqg' \
--header 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 Edg/98.0.1108.55' \
--header 'Content-Type: application/json;charset=UTF-8' \
--header 'Origin: http://www.financial-assistant.xyz' \
--header 'Referer: http://www.financial-assistant.xyz/' \
--header 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6' \
--header 'Content-Type: application/json' \
--data '{
	"text": "保收益",
	"level": 1,
	"category_name": "保证",
	"user": "君菁宜"
}'
"""

parser = Parser(curl_command)
# print(parser.parsed)
doc = parser.to_apidoc()
print(doc)
