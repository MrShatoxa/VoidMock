import random
import time

from common.base_mock import Mock

class GET_users(Mock):
    method = "GET"
    path = "/users"
    delay = 5 # задержка 5 секунд
    enabled = True
    rate_limit = 15000  # не более 15000 вызовов
    rate_limit_period = 1  # за 1 секунду

    async def get_response(self, request):
        return {"users": "123"}

mock = GET_users()