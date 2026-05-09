import random
from fastapi import Request
from common.base_mock import Mock

class POST_create_order(Mock):
    method = "POST"
    path = "/api/orders/{order_id}"
    delay = 0.2
    enabled = True

    async def get_response(self, request: Request):
        responses = [
            {"order_id": 1001, "status": "created", "amount": 1500},
            {"order_id": 1002, "status": "created", "amount": 2500},
        ]
        if request.query_params.get("add"):
            for i in responses:
                i["amount"] = i["amount"] + int(request.query_params["add"])
        if request.path_params["order_id"] == "1001":
            return responses[0]
        elif request.path_params["order_id"] == "1002":
            return responses[1]


mock = POST_create_order()