from typing import Any, Dict

from fastapi import status
from fastapi.responses import JSONResponse

from common.util.logging import LoggingUtil


logger = LoggingUtil.get_logger(__name__)


async def publish(payload: Dict[str, Any], topic: str) -> JSONResponse:
    try:
        from grid_services_api.app import redis_broker

        await redis_broker.connect()
        rpc_response_message = await redis_broker.request(message=payload, channel=topic)

        logger.info("Published grid function RPC to the redis broker.")

        # Decode the response message
        decoded_response = await rpc_response_message.decode()
        return JSONResponse(
            content=decoded_response,
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        logger.error("Error executing grid function broker publisher: %s", e)
        raise
