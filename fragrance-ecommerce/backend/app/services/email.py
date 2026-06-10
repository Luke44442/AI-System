"""Transactional and lifecycle email sending.

Uses SMTP when configured; logs the message in dev (never crashes a request).
All send_* functions accept plain data types — no ORM objects — so they can
be called from Celery tasks without loading DB models into worker processes.
"""
from __future__ import annotations
import logging
from decimal import Decimal
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared luxury base style
# ---------------------------------------------------------------------------
_BASE_STYLE = """
  body{margin:0;padding:0;background:#f5f5f0;font-family:Georgia,'Times New Roman',serif}
  .wrap{max-width:600px;margin:0 auto;background:#fff}
  .hdr{background:#0A0A0A;padding:28px 40px;text-align:center}
  .hdr a{font-family:Georgia,serif;font-size:22px;font-weight:normal;color:#C9A84C;
          text-decoration:none;letter-spacing:.15em}
  .body{padding:40px}
  .body h2{font-weight:normal;font-size:22px;margin:0 0 16px;color:#0A0A0A}
  .body p{color:#333;font-size:15px;line-height:1.7;margin:0 0 14px}
  .btn{display:inline-block;background:#C9A84C;color:#fff!important;padding:13px 28px;
       text-decoration:none;border-radius:3px;font-size:14px;letter-spacing:.05em;margin:8px 0}
  .item-table{width:100%;border-collapse:collapse;margin:20px 0}
  .item-table th{font-size:11px;text-transform:uppercase;letter-spacing:.1em;
                  color:#666;border-bottom:1px solid #e8e8e8;padding:6px 0;text-align:left}
  .item-table td{padding:10px 0;border-bottom:1px solid #f0f0f0;font-size:14px;color:#333}
  .total-row td{font-weight:bold;color:#0A0A0A;border-top:2px solid #0A0A0A;border-bottom:none}
  .ftr{background:#0A0A0A;padding:24px 40px;text-align:center}
  .ftr p{color:#666;font-size:12px;margin:4px 0;line-height:1.6}
  .ftr a{color:#C9A84C;text-decoration:none}
"""

_SITE_URL = "https://aurevia.com"
_SUPPORT_EMAIL = "support@aurevia.com"


def _html(body: str) -> str:
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>{_BASE_STYLE}</style></head><body>
<div class="wrap">
  <div class="hdr"><a href="{_SITE_URL}">AUREVIA</a></div>
  <div class="body">{body}</div>
  <div class="ftr">
    <p>© 2025 Aurevia — Luxury Authenticated.</p>
    <p><a href="{_SITE_URL}/policies/privacy">Privacy</a> &nbsp;·&nbsp;
       <a href="{_SITE_URL}/account/unsubscribe">Unsubscribe</a> &nbsp;·&nbsp;
       <a href="mailto:{_SUPPORT_EMAIL}">{_SUPPORT_EMAIL}</a></p>
  </div>
</div></body></html>"""


def _items_html(items: list[dict]) -> str:
    rows = ""
    for it in items:
        rows += f"""<tr>
          <td>{it.get('name','Item')}</td>
          <td style="text-align:center">{it.get('quantity',1)}</td>
          <td style="text-align:right">${float(it.get('unit_price',0)):.2f}</td>
        </tr>"""
    return f"""<table class="item-table">
      <thead><tr><th>Item</th><th style="text-align:center">Qty</th>
      <th style="text-align:right">Price</th></tr></thead>
      <tbody>{rows}</tbody></table>"""


# ---------------------------------------------------------------------------
# Core send helper
# ---------------------------------------------------------------------------

def send_email(to: str, subject: str, html_body: str, text_body: str | None = None) -> bool:
    """Send an email. Returns True if sent via SMTP, False if logged-only/failed."""
    if not (settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD):
        logger.info("EMAIL (not sent — SMTP unconfigured) to=%s subject=%s\n%s",
                    to, subject, text_body or html_body[:200])
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.EMAILS_FROM_EMAIL
    msg["To"] = to
    if text_body:
        msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAILS_FROM_EMAIL, [to], msg.as_string())
        logger.info("email_sent to=%s subject=%s", to, subject)
        return True
    except Exception as exc:
        logger.error("email_send_failed to=%s error=%s", to, exc)
        return False


# ---------------------------------------------------------------------------
# Auth emails
# ---------------------------------------------------------------------------

def send_password_reset_email(to: str, reset_url: str) -> bool:
    body = f"""
    <h2>Reset your password</h2>
    <p>We received a request to reset your Aurevia password. This link expires in 1 hour.</p>
    <p><a class="btn" href="{reset_url}">Reset Password</a></p>
    <p style="color:#999;font-size:13px">If you didn't request this, you can safely ignore this email.</p>"""
    return send_email(to, "Reset your Aurevia password", _html(body),
                      f"Reset your Aurevia password (expires 1 hour): {reset_url}")


def send_welcome_email(to: str, first_name: Optional[str] = None) -> bool:
    name = first_name or "there"
    body = f"""
    <h2>Welcome to Aurevia, {name}</h2>
    <p>You've joined the world of authenticated luxury — fragrances, sneakers, streetwear,
       designer bags, and more. Every piece we carry is verified for authenticity.</p>
    <p><a class="btn" href="{_SITE_URL}/products">Start Shopping</a></p>
    <p>Questions? Our team is always here at
       <a href="mailto:{_SUPPORT_EMAIL}">{_SUPPORT_EMAIL}</a>.</p>"""
    return send_email(to, "Welcome to Aurevia", _html(body),
                      f"Welcome to Aurevia, {name}. Start shopping: {_SITE_URL}/products")


# ---------------------------------------------------------------------------
# Order lifecycle emails
# ---------------------------------------------------------------------------

def send_order_confirmation_email(
    to: str,
    first_name: Optional[str],
    order_number: str,
    items: list[dict],
    subtotal: float,
    shipping: float,
    tax: float,
    discount: float,
    total: float,
    shipping_address: Optional[dict] = None,
) -> bool:
    name = first_name or "there"
    items_table = _items_html(items)

    addr_block = ""
    if shipping_address:
        addr_block = f"""<p style="font-size:14px;color:#555;margin:0 0 20px">
          Shipping to: {shipping_address.get('first_name','')} {shipping_address.get('last_name','')},
          {shipping_address.get('address1','')},
          {shipping_address.get('city','')} {shipping_address.get('state','')} {shipping_address.get('postal_code','')}
        </p>"""

    discount_row = f"<tr><td>Discount</td><td style='text-align:right'>-${discount:.2f}</td></tr>" if discount else ""

    body = f"""
    <h2>Order confirmed, {name}</h2>
    <p>Thank you for shopping with Aurevia. Your order <strong>{order_number}</strong> has been
       received and is now being prepared.</p>
    {items_table}
    <table style="width:100%;font-size:14px;color:#333">
      <tr><td>Subtotal</td><td style="text-align:right">${subtotal:.2f}</td></tr>
      <tr><td>Shipping</td><td style="text-align:right">${shipping:.2f}</td></tr>
      <tr><td>Tax</td><td style="text-align:right">${tax:.2f}</td></tr>
      {discount_row}
      <tr class="total-row"><td>Total</td><td style="text-align:right">${total:.2f}</td></tr>
    </table>
    {addr_block}
    <p><a class="btn" href="{_SITE_URL}/account/orders">View Order</a></p>
    <p style="font-size:13px;color:#999">We'll send a separate email with tracking once your order ships.</p>"""

    return send_email(
        to,
        f"Order confirmed — {order_number}",
        _html(body),
        f"Your Aurevia order {order_number} is confirmed. Total: ${total:.2f}",
    )


def send_shipping_notification_email(
    to: str,
    first_name: Optional[str],
    order_number: str,
    tracking_number: str,
    tracking_url: Optional[str] = None,
    carrier: Optional[str] = None,
) -> bool:
    name = first_name or "there"
    carrier_str = f" via {carrier}" if carrier else ""
    track_btn = (f'<p><a class="btn" href="{tracking_url}">Track Your Package</a></p>'
                 if tracking_url else f"<p>Tracking number: <strong>{tracking_number}</strong></p>")
    body = f"""
    <h2>Your order is on the way, {name}</h2>
    <p>Great news — order <strong>{order_number}</strong> has shipped{carrier_str}.</p>
    {track_btn}
    <p style="font-size:14px;color:#555">Tracking number: {tracking_number}</p>
    <p>Questions about your shipment? Contact us at
       <a href="mailto:{_SUPPORT_EMAIL}">{_SUPPORT_EMAIL}</a>.</p>"""

    return send_email(
        to,
        f"Your Aurevia order {order_number} has shipped",
        _html(body),
        f"Order {order_number} shipped. Track it: {tracking_url or tracking_number}",
    )


# ---------------------------------------------------------------------------
# Automation emails
# ---------------------------------------------------------------------------

def send_cart_abandonment_email(
    to: str,
    first_name: Optional[str],
    items: list[dict],
    cart_url: Optional[str] = None,
) -> bool:
    name = first_name or "there"
    url = cart_url or f"{_SITE_URL}/cart"
    preview = ", ".join(it.get("name", "item") for it in items[:3])
    if len(items) > 3:
        preview += f" +{len(items) - 3} more"

    items_table = _items_html(items)
    body = f"""
    <h2>You left something behind, {name}</h2>
    <p>Your cart is still waiting for you — {preview}.</p>
    {items_table}
    <p><a class="btn" href="{url}">Return to Cart</a></p>
    <p style="font-size:13px;color:#999">Your cart will be saved for 7 days.
       All items are authenticated and ready to ship.</p>"""

    return send_email(
        to,
        "Your Aurevia cart is waiting",
        _html(body),
        f"Hi {name}, you left items in your Aurevia cart: {preview}. Return: {url}",
    )


def send_review_request_email(
    to: str,
    first_name: Optional[str],
    order_number: str,
    items: list[dict],
) -> bool:
    name = first_name or "there"
    review_url = f"{_SITE_URL}/account/orders/{order_number}/review"
    preview = items[0].get("name", "your recent purchase") if items else "your recent purchase"
    body = f"""
    <h2>How's your {preview}?</h2>
    <p>Hi {name}, your Aurevia order <strong>{order_number}</strong> was delivered a week ago.
       We'd love to know what you think.</p>
    <p>Your review helps other customers find the perfect piece — and it only takes 60 seconds.</p>
    <p><a class="btn" href="{review_url}">Write a Review</a></p>
    <p style="font-size:13px;color:#999">Only reviewing items you purchased is required.
       Thank you for being part of the Aurevia community.</p>"""

    return send_email(
        to,
        f"How's your order, {name}? Leave a review",
        _html(body),
        f"Hi {name}, please review your Aurevia order {order_number}: {review_url}",
    )


def send_win_back_email(
    to: str,
    first_name: Optional[str],
    days_inactive: int,
    promo_code: Optional[str] = None,
) -> bool:
    name = first_name or "there"
    shop_url = f"{_SITE_URL}/products"
    promo_block = ""
    if promo_code:
        promo_block = f"""<p style="background:#f9f4e8;border-left:3px solid #C9A84C;
          padding:12px 16px;font-size:14px;margin:20px 0">
          Use code <strong>{promo_code}</strong> for 10% off your next order.</p>"""

    body = f"""
    <h2>We miss you, {name}</h2>
    <p>It's been a while since your last Aurevia order. We have new arrivals across
       fragrances, sneakers, streetwear, and accessories that we think you'll love.</p>
    {promo_block}
    <p><a class="btn" href="{shop_url}">See What's New</a></p>
    <p style="font-size:13px;color:#999">As always, every item is authenticated before it reaches you.</p>"""

    return send_email(
        to,
        f"New arrivals at Aurevia — we've missed you",
        _html(body),
        f"Hi {name}, check out new Aurevia arrivals: {shop_url}" + (f" Use code {promo_code} for 10% off." if promo_code else ""),
    )
