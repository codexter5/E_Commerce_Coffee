from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "BrewMart_User_Guide.pdf"


def paragraph(text, style):
    return Paragraph(text.replace("`", "<font name='Courier'>" if text.count("`") % 2 else ""), style)


def footer(canvas, document):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D9D2C7"))
    canvas.line(18 * mm, 14 * mm, 192 * mm, 14 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#756E66"))
    canvas.drawString(18 * mm, 9 * mm, "BrewMart User Guide | Demonstration system")
    canvas.drawRightString(192 * mm, 9 * mm, f"Page {document.page}")
    canvas.restoreState()


def build():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=30, leading=36, alignment=TA_CENTER, textColor=colors.HexColor("#3A2419"), spaceAfter=12))
    styles.add(ParagraphStyle(name="CoverSub", parent=styles["Normal"], fontSize=13, leading=19, alignment=TA_CENTER, textColor=colors.HexColor("#756E66")))
    styles.add(ParagraphStyle(name="GuideH1", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=19, leading=23, textColor=colors.HexColor("#3A2419"), spaceBefore=12, spaceAfter=8))
    styles.add(ParagraphStyle(name="GuideH2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12, leading=15, textColor=colors.HexColor("#7A452C"), spaceBefore=8, spaceAfter=5))
    styles.add(ParagraphStyle(name="GuideBody", parent=styles["BodyText"], fontSize=10, leading=15, textColor=colors.HexColor("#302B27"), spaceAfter=7))
    styles.add(ParagraphStyle(name="GuideSmall", parent=styles["BodyText"], fontSize=8.5, leading=12, textColor=colors.HexColor("#756E66")))
    styles.add(ParagraphStyle(name="Callout", parent=styles["BodyText"], fontSize=10, leading=15, textColor=colors.HexColor("#3A2419"), backColor=colors.HexColor("#F3E8DA"), borderColor=colors.HexColor("#D9B58D"), borderWidth=0.7, borderPadding=9, spaceBefore=6, spaceAfter=10))
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=17 * mm, bottomMargin=20 * mm, title="BrewMart User Guide", author="BrewMart")
    story = [Spacer(1, 38 * mm), Paragraph("BrewMart", styles["CoverTitle"]), Paragraph("User Guide", styles["CoverTitle"]), Spacer(1, 8 * mm), Paragraph("Shopping, demo payments, digital wallets, and peer-to-peer transfers", styles["CoverSub"]), Spacer(1, 18 * mm), Paragraph("Local demonstration edition", styles["CoverSub"]), PageBreak()]
    story.append(Paragraph("Purpose", styles["GuideH1"]))
    story.append(Paragraph("BrewMart is a Django coffee shop application with user accounts, product browsing, shopping carts, wishlists, reviews, order history, a simulated Nepali payment gateway, and a stored-value digital wallet.", styles["GuideBody"]))
    story.append(Paragraph("The payment gateway and wallet features are demonstrations for local development. They do not move real money.", styles["Callout"]))
    story.append(Paragraph("Start the application", styles["GuideH1"]))
    for index, text in enumerate(["Open a terminal in the project directory.", "Activate the virtual environment if one is configured.", "Install dependencies with <font name='Courier'>pip install -r requirements.txt</font>.", "Apply migrations with <font name='Courier'>python manage.py migrate</font>.", "Start the site with <font name='Courier'>python manage.py runserver</font>.", "Open <font name='Courier'>http://localhost:8000/</font>."]):
        story.append(Paragraph(f"{index + 1}. {text}", styles["GuideBody"]))
    story.append(Paragraph("Customer account", styles["GuideH1"]))
    for text in ["Select <b>Register</b> and create an account.", "Sign in using the account credentials.", "Open <b>Account</b> to update profile and shipping details.", "The account receives a digital wallet automatically with a zero balance."]:
        story.append(Paragraph("• " + text, styles["GuideBody"]))
    story.append(PageBreak())
    story.append(Paragraph("Shopping and checkout", styles["GuideH1"]))
    for index, text in enumerate(["Open <b>Shop</b> or a product category.", "Open a product and add it to the cart.", "Open <b>Cart</b>, review quantities, and select checkout.", "Sign in if requested.", "Enter delivery and contact details, then select <b>Continue to payment</b>."]):
        story.append(Paragraph(f"{index + 1}. {text}", styles["GuideBody"]))
    story.append(Paragraph("Demo card payment", styles["GuideH1"]))
    story.append(Paragraph("The payment page is a local Khalti-style simulator. It does not contact Khalti, a bank, or a card network.", styles["GuideBody"]))
    card_data = [[Paragraph("Field", styles["GuideBody"]), Paragraph("Demo value", styles["GuideBody"])], ["Cardholder name", "Any name"], ["Card number", "4111 1111 1111 1111"], ["Expiry", "12/30"], ["CVV", "123"]]
    table = Table(card_data, colWidths=[55 * mm, 105 * mm])
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3A2419")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D9D2C7")), ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#FBF8F3")), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTNAME", (1, 2), (1, 3), "Courier"), ("FONTNAME", (1, 4), (1, 4), "Courier"), ("FONTSIZE", (0, 0), (-1, -1), 9), ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    story.extend([table, Spacer(1, 6 * mm), Paragraph("Select <b>Pay</b>. A successful response displays a <font name='Courier'>KHALTI-DEMO-...</font> reference, creates the order, reduces product stock, and clears the cart.", styles["GuideBody"]), Paragraph("To demonstrate a declined payment, enter any other card number. The cart remains unchanged and no order is created.", styles["GuideBody"]), Paragraph("Card number and CVV are used only for the request and are never stored by this application.", styles["Callout"])])
    story.append(PageBreak())
    story.append(Paragraph("Digital wallet", styles["GuideH1"]))
    story.append(Paragraph("The wallet is a stored-value balance denominated in Nepalese rupees. A wallet is created automatically for every new account. Existing accounts receive one when the wallet migration is applied.", styles["GuideBody"]))
    story.append(Paragraph("Fund a wallet for demonstration", styles["GuideH2"]))
    for index, text in enumerate(["Sign in to the Django admin at <font name='Courier'>http://localhost:8000/admin/</font>.", "Open <b>Wallets</b>.", "Select a user's wallet and enter a demonstration balance.", "Save the wallet."]):
        story.append(Paragraph(f"{index + 1}. {text}", styles["GuideBody"]))
    story.append(Paragraph("Only an administrator should fund wallets in this demonstration. There is no real deposit or withdrawal integration.", styles["Callout"]))
    story.append(Paragraph("Transfer between two accounts", styles["GuideH2"]))
    for index, text in enumerate(["Create or use two customer accounts.", "Fund the sender's wallet from the admin panel.", "Sign in as the sender.", "Open <b>Account</b>, then <b>Open wallet and transfer funds</b>.", "Enter the recipient's username, amount, and an optional note.", "Select <b>Send funds</b>.", "Review the balance and transfer reference in wallet history."]):
        story.append(Paragraph(f"{index + 1}. {text}", styles["GuideBody"]))
    story.append(Paragraph("The sender's balance decreases and the recipient's balance increases in one database transaction. Oversized transfers, unknown recipients, and self-transfers are rejected. Each successful transfer receives a unique <font name='Courier'>WAL-...</font> reference.", styles["GuideBody"]))
    story.append(PageBreak())
    story.append(Paragraph("Useful routes", styles["GuideH1"]))
    routes = [["Route", "Use"], ["/", "Home page"], ["/products/", "Product catalogue"], ["/cart/", "Shopping cart"], ["/orders/checkout/", "Delivery details"], ["/orders/payment/", "Demo card payment"], ["/orders/history/", "Customer order history"], ["/accounts/register/", "Create an account"], ["/accounts/profile/", "Profile and wallet balance"], ["/accounts/wallet/", "Wallet transfers and history"], ["/admin/", "Product, order, and wallet administration"]]
    route_table = Table(routes, colWidths=[60 * mm, 100 * mm])
    route_table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3A2419")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D9D2C7")), ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#FBF8F3")), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTNAME", (0, 1), (0, -1), "Courier"), ("FONTSIZE", (0, 0), (-1, -1), 8.5), ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    story.append(route_table)
    story.append(Paragraph("Important production boundary", styles["GuideH1"]))
    story.append(Paragraph("Before production use, replace the local gateway simulator with the official Khalti or eSewa integration. Create a pending order, send the customer to the gateway, verify the server-side callback or lookup response, and only then finalize payment, stock, and order status. Never store full card numbers or CVV values.", styles["Callout"]))
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


if __name__ == "__main__":
    build()
    print(OUTPUT)