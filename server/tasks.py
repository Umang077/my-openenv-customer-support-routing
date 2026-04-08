"""
All ticket data for all three tasks.
Correct answers are stored here (server-side only — never sent to the agent).
"""

from typing import TypedDict, List, Dict


class TicketData(TypedDict):
    id: str
    subject: str
    text: str
    correct_team: str
    correct_priority: str


class TaskConfig(TypedDict):
    name: str
    difficulty: str
    tickets: List[TicketData]
    team_weight: float
    priority_weight: float


AVAILABLE_TEAMS = ["billing", "technical", "returns", "general_inquiry", "security"]
AVAILABLE_PRIORITIES = ["low", "medium", "high"]


# ── TASK 1 : simple_routing (Easy) ────────────────────────────────────────────
# Tickets have obvious, unambiguous keywords. Priority is NOT evaluated.

SIMPLE_ROUTING_TICKETS: List[TicketData] = [
    {
        "id": "T001",
        "subject": "Double charge on my credit card",
        "text": (
            "Hi, I noticed my credit card was charged twice for order #12345 placed "
            "yesterday. Both charges are $49.99. I only placed one order. "
            "Please refund the duplicate charge as soon as possible."
        ),
        "correct_team": "billing",
        "correct_priority": "medium",
    },
    {
        "id": "T002",
        "subject": "Mobile app keeps crashing on startup",
        "text": (
            "Your mobile app crashes every single time I try to open the dashboard. "
            "I have reinstalled it three times and the problem persists. "
            "I am on iOS 17 running on an iPhone 14. This is a technical issue I need fixed."
        ),
        "correct_team": "technical",
        "correct_priority": "medium",
    },
    {
        "id": "T003",
        "subject": "I want to return my purchase",
        "text": (
            "I would like to return the laptop bag I ordered last week (order #67890). "
            "It does not match what was shown in the product photos. "
            "The item is still in its original packaging and unused. "
            "How do I start the return process?"
        ),
        "correct_team": "returns",
        "correct_priority": "low",
    },
    {
        "id": "T004",
        "subject": "What are your store opening hours?",
        "text": (
            "Hi there, I am planning to visit your store this weekend. "
            "Could you please let me know your opening and closing times? "
            "Do you open on Sundays? Also, is there parking available nearby?"
        ),
        "correct_team": "general_inquiry",
        "correct_priority": "low",
    },
    {
        "id": "T005",
        "subject": "My account was hacked — locked out",
        "text": (
            "URGENT: Someone has logged into my account from an unknown location in Russia. "
            "They changed my password and I am now completely locked out. "
            "My account has saved payment methods and personal data. "
            "Please help me regain access and secure my account immediately!"
        ),
        "correct_team": "security",
        "correct_priority": "high",
    },
]


# ── TASK 2 : priority_routing (Medium) ───────────────────────────────────────
# Both team AND priority are evaluated. Some tickets have urgency cues.

PRIORITY_ROUTING_TICKETS: List[TicketData] = [
    {
        "id": "T101",
        "subject": "Possibly fraudulent transaction on my account",
        "text": (
            "There is a $450 charge from a retailer I have never heard of. "
            "I suspect someone has stolen my card details. "
            "Please block my card and open a fraud investigation immediately. "
            "This is extremely urgent as more charges may follow."
        ),
        "correct_team": "billing",
        "correct_priority": "high",
    },
    {
        "id": "T102",
        "subject": "Website loads a bit slowly sometimes",
        "text": (
            "Just a heads-up — your product listing pages have been taking about "
            "8 to 10 seconds to load for the past few days. "
            "It is not a big deal and I can still use the site. "
            "Could be my internet connection, but thought I would flag it."
        ),
        "correct_team": "technical",
        "correct_priority": "low",
    },
    {
        "id": "T103",
        "subject": "Return inquiry for purchase made 6 months ago",
        "text": (
            "I bought a mechanical keyboard about six months ago and the spacebar "
            "key has started sticking. I know it is likely past the standard return window "
            "but wanted to ask if there are any warranty or exception options. "
            "No urgency at all, just checking."
        ),
        "correct_team": "returns",
        "correct_priority": "low",
    },
    {
        "id": "T104",
        "subject": "Payment API throwing 403 errors — product launch in 48 hours",
        "text": (
            "We are integrating your payment API into our checkout flow and are getting "
            "403 Forbidden errors on every single API call. "
            "We have double-checked all API keys and followed the documentation exactly. "
            "Our product launches in 48 hours and this is completely blocking our release. "
            "We need urgent technical support."
        ),
        "correct_team": "technical",
        "correct_priority": "high",
    },
    {
        "id": "T105",
        "subject": "Promo code not applied and wrong colour item shipped",
        "text": (
            "My invoice shows $89.99 but with my promo code SAVE20 it should be $69.99. "
            "The discount was not applied at checkout. "
            "Additionally, I ordered the blue model but received the black one. "
            "Please correct the billing charge and advise on the wrong item."
        ),
        "correct_team": "billing",
        "correct_priority": "medium",
    },
    {
        "id": "T106",
        "subject": "Cannot reset password and seeing a suspicious login",
        "text": (
            "I have been trying to reset my password for over two hours. "
            "The reset emails are not arriving even after checking spam. "
            "More worryingly, I can see in my recent activity log a login from "
            "Singapore at 3am, and I have never been there. "
            "Please lock my account and help me regain access urgently."
        ),
        "correct_team": "security",
        "correct_priority": "high",
    },
]


# ── TASK 3 : batch_routing (Hard) ────────────────────────────────────────────
# Subject lines are deliberately misleading. Agent must read the full message body.

BATCH_ROUTING_TICKETS: List[TicketData] = [
    {
        "id": "T201",
        "subject": "General question about my account",  # misleading: sounds like general_inquiry
        "text": (
            "Hey, just a quick question — when does my monthly subscription renew? "
            "I want to make sure I have enough balance in my payment method. "
            "Also, do you offer annual billing plans that might save money?"
        ),
        "correct_team": "billing",       # subscription/payment = billing, NOT general_inquiry
        "correct_priority": "low",
    },
    {
        "id": "T202",
        "subject": "Technical issue with my return",  # misleading: says "technical"
        "text": (
            "I started a return for order #33211 last week and was supposed to receive "
            "an email with a prepaid shipping label. I never got it — checked spam too. "
            "My return window closes in exactly 3 days so I need this resolved soon."
        ),
        "correct_team": "returns",       # return process problem, NOT a technical bug
        "correct_priority": "medium",
    },
    {
        "id": "T203",
        "subject": "Account access issue",  # could sound like security but it is NOT
        "text": (
            "I forgot my password and the reset link in the email says it has already expired. "
            "I have tried five times over the past day with the same result. "
            "I need to access my order history to pull invoices for my tax filing "
            "which is due in about two weeks."
        ),
        "correct_team": "technical",     # password reset flow = technical, NOT security (no breach)
        "correct_priority": "medium",
    },
    {
        "id": "T204",
        "subject": "Product arrived broken",
        "text": (
            "My order arrived this morning and the screen was cracked inside the sealed box. "
            "I photographed everything right after unboxing as evidence. "
            "This was meant to be a birthday gift for tomorrow's party. "
            "I urgently need an immediate replacement or same-day refund."
        ),
        "correct_team": "returns",
        "correct_priority": "high",      # high because of 1-day time pressure
    },
    {
        "id": "T205",
        "subject": "Suspicious email about my billing details",  # mentions billing but is security
        "text": (
            "I received an email asking me to urgently verify my billing information. "
            "The sender address looks suspicious and the company logo looks slightly off. "
            "I have not clicked any links. Is this a phishing attempt? "
            "Should I be worried about my account being compromised?"
        ),
        "correct_team": "security",      # phishing report = security, NOT billing
        "correct_priority": "high",
    },
    {
        "id": "T206",
        "subject": "Refund received but the amount is wrong",
        "text": (
            "You processed my return for RMA #4421 last week and I received a refund "
            "of $23.50. However, I originally paid $45.99 and the return was approved in full. "
            "The partial refund amount is incorrect. Please review and correct this."
        ),
        "correct_team": "billing",       # refund dispute after return is complete = billing
        "correct_priority": "medium",
    },
    {
        "id": "T207",
        "subject": "Cannot view my billing history",  # billing in subject but root cause is technical
        "text": (
            "Every time I tap on the Billing section in your Android app, it crashes immediately. "
            "I cannot see any invoices or past payment records at all. "
            "This has been happening for about a week. "
            "I am on a Samsung Galaxy S23 running Android 14."
        ),
        "correct_team": "technical",     # app crash = technical, even though billing is mentioned
        "correct_priority": "medium",
    },
    {
        "id": "T208",
        "subject": "A few minor questions",
        "text": (
            "Nothing urgent, just a few small things: "
            "(1) My last invoice looks about $12 higher than usual — not sure why. "
            "(2) Do you offer enterprise or bulk pricing for teams? "
            "(3) Can I return a gift I bought for someone else? "
            "Thanks, no rush on any of these."
        ),
        "correct_team": "billing",       # primary issue is the billing discrepancy (item 1)
        "correct_priority": "low",
    },
]


# ── Task registry ─────────────────────────────────────────────────────────────

TASKS: Dict[str, TaskConfig] = {
    "simple_routing": {
        "name": "simple_routing",
        "difficulty": "easy",
        "tickets": SIMPLE_ROUTING_TICKETS,
        "team_weight": 1.0,
        "priority_weight": 0.0,   # priority not evaluated in easy task
    },
    "priority_routing": {
        "name": "priority_routing",
        "difficulty": "medium",
        "tickets": PRIORITY_ROUTING_TICKETS,
        "team_weight": 0.6,
        "priority_weight": 0.4,
    },
    "batch_routing": {
        "name": "batch_routing",
        "difficulty": "hard",
        "tickets": BATCH_ROUTING_TICKETS,
        "team_weight": 0.5,
        "priority_weight": 0.5,
    },
}