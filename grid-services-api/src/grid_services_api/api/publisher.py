"""
This module provides a utility function for publishing RPC payloads to a Redis broker.

It encapsulates the logic for connecting to Redis, sending messages, and handling
responses for various grid service functions.
"""

from typing import Any, Dict

from fastapi import status
from fastapi.responses import JSONResponse

from common.util.logging import LoggingUtil


logger = LoggingUtil.get_logger(__name__)


async def publish(payload: Dict[str, Any], topic: str) -> JSONResponse:
    """
    Publishes an RPC payload to a specified Redis topic and awaits a response.

    This asynchronous function connects to the Redis broker, sends the RPC
    `payload` to the given `topic`, and then waits for a response. The response
    message is decoded and returned as a JSONResponse. Error logging is
    included for publishing failures.

    Args:
        payload (Dict[str, Any]): The RPC payload to be published. This dictionary
                                   should contain the 'method' and 'params' for the RPC call.
        topic (str): The Redis topic to which the payload will be published.

    Returns:
        JSONResponse: A FastAPI JSONResponse containing the decoded RPC response
                      message and an HTTP 200 OK status if successful.

    Raises:
        Exception: Re-raises any exception encountered during the publishing
                   or response decoding process after logging the error.
    """
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
