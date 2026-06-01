import requests
from utils.logger import log
from config.settings import BASE_URL

class HttpClient:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()  # 全局会话，自动带 token

    def request(self, method, url, **kwargs):
        full_url = self.base_url + url
        log.info(f"请求地址: {full_url}")
        log.info(f"请求方式: {method}")
        log.info(f"请求头: {dict(self.session.headers)}")
        log.info(f"请求参数: {kwargs}")

        try:
            resp = self.session.request(method, full_url, **kwargs)
            log.info(f"响应状态码: {resp.status_code}")
            log.info(f"响应内容: {resp.text}")
            return resp
        except Exception as e:
            log.error(f"请求异常: {str(e)}")
            raise

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)

http = HttpClient()