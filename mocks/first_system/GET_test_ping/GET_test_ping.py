from common.base_mock import Mock

class GET_test_ping(Mock):
    method = "GET"
    path = "/ping"
    delay = 0
    enabled = True

    async def get_response(self, request):
        return {"status": "ok", "message": "pong"}
mock = GET_test_ping()