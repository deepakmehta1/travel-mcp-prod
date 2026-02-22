import logging
import logging.config
import os
from datetime import datetime, timezone
from uuid import uuid4

from fastmcp import FastMCP
from pydantic import BaseModel, Field, ValidationError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGGING_CONF = os.path.join(BASE_DIR, "logging.conf")

if os.path.exists(LOGGING_CONF):
    logging.config.fileConfig(LOGGING_CONF)
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("payment-agent")

mcp = FastMCP(name="Payment Agent MCP Server")


class PaymentRequest(BaseModel):
    customer_id: int = Field(ge=1)
    amount: int = Field(ge=1)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    method: str = Field(default="card", min_length=2)
    consent: bool


class PaymentResponse(BaseModel):
    success: bool
    receipt: dict | None = None
    error: str | None = None


@mcp.tool()
def processPayment(
    customer_id: int,
    amount: int,
    currency: str = "INR",
    method: str = "card",
    consent: bool = False,
) -> dict:
    try:
        req = PaymentRequest(
            customer_id=customer_id,
            amount=amount,
            currency=currency,
            method=method,
            consent=consent,
        )
    except ValidationError as exc:
        logger.warning("Invalid request", extra={"errors": exc.errors()})
        return PaymentResponse(success=False, error="INVALID_REQUEST").model_dump()

    if not req.consent:
        logger.info("Payment consent missing", extra={"customer_id": req.customer_id})
        return PaymentResponse(success=False, error="CONSENT_REQUIRED").model_dump()

    receipt = {
        "payment_id": f"pay_{uuid4().hex}",
        "customer_id": req.customer_id,
        "amount": req.amount,
        "currency": req.currency,
        "method": req.method,
        "status": "PAID",
        "paid_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("Payment processed", extra={"payment_id": receipt["payment_id"]})
    return PaymentResponse(success=True, receipt=receipt).model_dump()


def main() -> None:
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "9002"))

    if transport == "streamable-http":
        logger.info("Starting Payment Agent MCP Server", extra={"host": host, "port": port, "transport": "streamable-http"})
        mcp.run(transport="streamable-http", host=host, port=port)
    else:
        logger.info("Starting Payment Agent MCP Server (stdio mode)")
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
