from dataclasses import dataclass
from decimal import Decimal
from uuid import uuid4


@dataclass
class PaymentResult:
    successful: bool
    reference: str
    message: str


class BaseDemoGateway:
    """Base class for local payment simulators. None of these contact a real payment network."""

    name = "Demo Gateway"


class DummyCardGateway(BaseDemoGateway):
    """Local credit/debit card simulator."""

    name = "Card Payment (Demo)"
    demo_card_number = "4111111111111111"
    demo_expiry = "12/30"
    demo_cvv = "123"

    def charge(self, amount: Decimal, card_number: str, expiry: str, cvv: str) -> PaymentResult:
        if (
            card_number.replace(" ", "") == self.demo_card_number
            and expiry == self.demo_expiry
            and cvv == self.demo_cvv
        ):
            return PaymentResult(True, f"CARD-DEMO-{uuid4().hex[:10].upper()}", f"Rs. {amount} payment approved")
        return PaymentResult(False, "", "Payment declined. Use the demo card details shown on this page.")


class DummyKhaltiGateway(BaseDemoGateway):
    """Local Khalti-style wallet simulator; it never contacts a payment network."""

    name = "Khalti"
    demo_khalti_id = "9800000000"
    demo_pin = "1111"

    def charge(self, amount: Decimal, khalti_id: str, pin: str) -> PaymentResult:
        if khalti_id.strip() == self.demo_khalti_id and pin == self.demo_pin:
            return PaymentResult(
                True, f"KHALTI-DEMO-{uuid4().hex[:10].upper()}", f"Rs. {amount} payment approved via Khalti"
            )
        return PaymentResult(False, "", "Payment declined. Use the demo Khalti ID and MPIN shown on this page.")


class DummyEsewaGateway(BaseDemoGateway):
    """Local eSewa-style wallet simulator; it never contacts a payment network."""

    name = "eSewa"
    demo_esewa_id = "9800000001"
    demo_password = "Nepal@123"
    demo_otp = "123456"

    def charge(self, amount: Decimal, esewa_id: str, password: str, otp: str) -> PaymentResult:
        if esewa_id.strip() == self.demo_esewa_id and password == self.demo_password and otp == self.demo_otp:
            return PaymentResult(
                True, f"ESEWA-DEMO-{uuid4().hex[:10].upper()}", f"Rs. {amount} payment approved via eSewa"
            )
        return PaymentResult(False, "", "Payment declined. Use the demo eSewa ID, password and token shown on this page.")


class CashOnDeliveryGateway(BaseDemoGateway):
    """No upfront payment is collected; the buyer pays the delivery person in cash."""

    name = "Cash on Delivery"

    def charge(self, amount: Decimal) -> PaymentResult:
        return PaymentResult(True, f"COD-{uuid4().hex[:10].upper()}", f"Rs. {amount} to be collected on delivery")
