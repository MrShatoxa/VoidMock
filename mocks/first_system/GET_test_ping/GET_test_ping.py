import random
from common.base_mock import Mock

class GET_test_ping(Mock):
    method = "GET"
    path = "/ping"
    delay = 0.5
    enabled = True
    rate_limit = 5  # не более 5 вызовов
    rate_limit_period = 1  # за 1 секунду

    async def get_response(self, request):
        file_pool = self.get_data_files_list(".json")
        rand_file = random.choice(file_pool)
        users = self.load_data_file(rand_file)
        return users

mock = GET_test_ping()