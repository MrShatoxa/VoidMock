import random
from fastapi import Request
from common.base_mock import Mock

class POST_create_order(Mock):
    method = "POST"
    path = "/api/orders"
    delay = 0.2
    enabled = True

    async def get_response(self, request: Request):
        responses = [
            {"order_id": 1001, "status": "created", "amount": 1500},
            {"order_id": 1002, "status": "created", "amount": 2500},
        ]
        return random.choice(responses)

mock = POST_create_order(mock_name="first_system.POST_create_order")