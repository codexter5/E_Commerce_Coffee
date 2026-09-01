from dataclasses import dataclass
from decimal import Decimal
from uuid import uuid4


@dataclass
class PaymentResult:
    successful: bool
    reference: str
    message: str


class DummyKhaltiGateway:
    """Local Khalti-style gateway simulator; it never contacts a payment network."""

    name = "Khalti Demo Gateway"
    demo_card_number = "4111111111111111"
    demo_expiry = "12/30"
    demo_cvv = "123"

    def charge(self, amount: Decimal, card_number: str, expiry: str, cvv: str) -> PaymentResult:
        if (
            card_number.replace(" ", "") == self.demo_card_number
            and expiry == self.demo_expiry
            and cvv == self.demo_cvv
        ):
            return PaymentResult(True, f"KHALTI-DEMO-{uuid4().hex[:10].upper()}", f"Rs. {amount} payment approved")
        return PaymentResult(False, "", "Payment declined. Use the demo card details shown on this page.")