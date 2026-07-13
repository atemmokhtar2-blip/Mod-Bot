"""
Telegram Stars donations — Version 5.

Namespace: donate

Callback patterns
------------------
donate:menu          — show donation amount picker
donate:cancel         — cancel and return home
donate:pay:{amount}   — send a real Telegram Stars invoice for {amount} XTR

Payment flow (real Telegram Stars — no simulated/fake payments)
-----------------------------------------------------------------
1. User taps an amount → bot.send_invoice(currency="XTR", provider_token="", ...)
2. Telegram sends a PreCheckoutQuery → we approve it (ok=True)
3. Telegram sends a successful_payment message → we record the donation in
   PostgreSQL and thank the user.
"""

from __future__ import annotations

from aiogram import Bot, Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    CallbackQuery,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.builder import back_kb, donate_amounts_kb, main_menu_kb
from bot.strings.ar import S
from database import repository as repo
from utils.helpers import escape_html
from utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="donations")


async def _answer(cb: CallbackQuery, text: str = "✅") -> None:
    try:
        await cb.answer(text)
    except Exception:
        pass


async def _edit(cb: CallbackQuery, text: str, reply_markup=None) -> None:
    try:
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=reply_markup)
    except TelegramBadRequest:
        pass


# ---------------------------------------------------------------------------
# Donation menu
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "donate:menu")
async def cb_donate_menu(cb: CallbackQuery) -> None:
    await _answer(cb)
    await _edit(cb, S.donate_title, reply_markup=donate_amounts_kb())


@router.callback_query(F.data == "donate:cancel")
async def cb_donate_cancel(cb: CallbackQuery) -> None:
    """User cancelled the donation flow before an invoice was sent."""
    await _answer(cb)
    await _edit(cb, S.donate_cancelled, reply_markup=back_kb("menu:home"))


# ---------------------------------------------------------------------------
# Send the real Telegram Stars invoice
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("donate:pay:"))
async def cb_donate_pay(cb: CallbackQuery, bot: Bot) -> None:
    await _answer(cb)
    try:
        amount = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        return
    if amount <= 0:
        return

    payload = f"donate:{cb.from_user.id}:{amount}:{cb.id}"

    try:
        await bot.send_invoice(
            chat_id=cb.from_user.id,
            title=S.donate_invoice_title,
            description=S.donate_invoice_description.format(amount=amount),
            payload=payload,
            currency="XTR",
            prices=[LabeledPrice(label=S.donate_invoice_label.format(amount=amount), amount=amount)],
            provider_token="",  # Telegram Stars payments do not use a provider token
        )
    except Exception as exc:
        log.warning("Failed to send Stars invoice to %s: %s", cb.from_user.id, exc)
        try:
            await cb.message.answer(S.donate_invoice_failed)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Pre-checkout — must be answered within 10s or Telegram cancels the payment
# ---------------------------------------------------------------------------

@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery, bot: Bot) -> None:
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


# ---------------------------------------------------------------------------
# Successful payment — record donation + thank the user
# ---------------------------------------------------------------------------

@router.message(F.successful_payment)
async def process_successful_payment(message: Message, session: AsyncSession) -> None:
    payment = message.successful_payment
    if not payment or payment.currency != "XTR":
        return

    user = message.from_user
    amount = payment.total_amount  # Stars amounts are already integer units (no /100)

    await repo.create_pending_donation(
        session,
        user_id=user.id,
        amount=amount,
        payload=payment.invoice_payload,
        currency=payment.currency,
    )
    await repo.mark_donation_paid(
        session,
        payload=payment.invoice_payload,
        telegram_charge_id=payment.telegram_payment_charge_id,
        provider_charge_id=payment.provider_payment_charge_id,
    )

    await repo.upsert_user(
        session,
        user_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
    )

    log.info("Received %s XTR donation from user %s", amount, user.id)

    await message.answer(
        S.donate_thanks.format(amount=amount),
        parse_mode="HTML",
    )
