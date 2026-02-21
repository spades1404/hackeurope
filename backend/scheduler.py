"""
Task Scheduler Service

Runs as a background async loop (or standalone process).
Periodically checks the `actions` table for upcoming deadlines and:
1. When deadline is <=30 days away and no document exists → trigger AI generation
2. When deadline is <=7 days away and document is still draft → escalate priority
3. When deadline has passed and status is not 'submitted' → mark as overdue
4. Logs all actions to `agent_audit_log`

Task lifecycle:
  upcoming → in_progress (AI generating) → pending_review (draft ready) → approved → submitted
  At any point: → overdue (if deadline passes)
"""

import asyncio
from datetime import date, datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger("scheduler")

# ── Configuration ────────────────────────────────────────────

CHECK_INTERVAL_SECONDS = 300         # Check every 5 minutes (adjustable)
AUTO_GENERATE_DAYS_BEFORE = 30       # Generate docs this many days before deadline
ESCALATE_DAYS_BEFORE = 7             # Escalate priority this many days before
OVERDUE_GRACE_DAYS = 0               # Days after deadline before marking overdue

# ── Core Loop ────────────────────────────────────────────────

async def scheduler_loop(
    db,              # database module
    agent_generate,  # async function(company_id, action_id) -> document
):
    """
    Main scheduler loop. Call this as a background task.
    """
    logger.info("Scheduler started. Checking every %ds", CHECK_INTERVAL_SECONDS)

    while True:
        try:
            await run_check_cycle(db, agent_generate)
        except Exception as e:
            logger.error("Scheduler cycle error: %s", e)

        await asyncio.sleep(CHECK_INTERVAL_SECONDS)


async def run_check_cycle(db, agent_generate):
    """Single check cycle — can also be called manually via API."""
    today = date.today()
    companies = await db.list_companies()

    for company in companies:
        company_id = company["id"]
        actions = await db.list_actions(company_id)

        for action in actions:
            deadline = date.fromisoformat(action["deadline"])
            days_until = (deadline - today).days
            status = action["status"]

            # ── OVERDUE CHECK ────────────────────────────
            if days_until < -OVERDUE_GRACE_DAYS and status not in ("submitted", "overdue"):
                await db.update_action_status(action["id"], "overdue")
                logger.warning(
                    "OVERDUE: %s (%s) — %d days past deadline",
                    action["obligation_name"], action["jurisdiction"], abs(days_until)
                )
                continue

            # ── AUTO-GENERATE CHECK ──────────────────────
            if (
                days_until <= AUTO_GENERATE_DAYS_BEFORE
                and status == "upcoming"
                and not action.get("document_id")
            ):
                logger.info(
                    "AUTO-GENERATING: %s (%s) — %d days until deadline",
                    action["obligation_name"], action["jurisdiction"], days_until
                )
                await db.update_action_status(action["id"], "in_progress")

                try:
                    document = await agent_generate(company_id, action["id"])
                    if document and not document.get("error"):
                        doc_id = await db.create_document(
                            doc_id=document.get("document_id", ""),  # Assuming agent_generate returns it
                            action_id=action["id"],
                            company_id=company_id,
                            document_type=action.get("output_type", "tax_return"),
                            content=document,
                            status="draft"
                        )
                        await db.update_action_document(action["id"], doc_id)
                        await db.update_action_status(action["id"], "pending_review")
                        logger.info("Document generated: %s → %s", action["obligation_name"], doc_id)
                    else:
                        error_msg = document.get("error", "Unknown error") if document else "No response"
                        logger.error("Generation failed for %s: %s", action["obligation_name"], error_msg)
                        await db.update_action_status(action["id"], "upcoming")  # Reset to retry next cycle
                except Exception as e:
                    logger.error("Exception generating %s: %s", action["obligation_name"], e)
                    await db.update_action_status(action["id"], "upcoming")

            # ── ESCALATION CHECK ─────────────────────────
            if days_until <= ESCALATE_DAYS_BEFORE and status == "pending_review":
                current_priority = action.get("priority", "medium")
                if current_priority not in ("critical", "overdue"):
                    await db.update_action_priority(action["id"], "critical")
                    logger.warning(
                        "ESCALATED: %s (%s) — only %d days left, still pending review",
                        action["obligation_name"], action["jurisdiction"], days_until
                    )

    logger.info("Check cycle complete at %s", datetime.now().isoformat())
