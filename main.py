"""
Devlancer Multi-Tenant AI Chatbot SaaS Platform
Central microservice managing multi-tenant holiday concierges, universal embeddable widgets,
lead extraction, and real-time CRM syncing.
"""

import os
import time
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from google import genai
import httpx
from dotenv import load_dotenv

# Local platform modules
from database import (
    init_db,
    get_tenant_by_id,
    get_tenant_by_slug,
    get_tenant_by_assistant_id,
    get_tenant_by_domain,
    list_all_tenants,
    upsert_tenant,
    delete_tenant,
    get_tenant_packages,
    set_tenant_packages,
    save_turn,
    get_conversation_history,
    list_tenant_conversations,
    get_conversation_messages,
    insert_lead,
    list_tenant_leads,
    count_tenant_leads,
    get_platform_analytics,
    verify_tenant_installation,
    update_tenant_settings,
    delete_lead,
    delete_conversation_data,
    save_feedback,
    get_session_context,
    upsert_session_context,
    clear_session_context,
    log_unanswered_question,
    list_unanswered_questions,
    list_feedback,
)
from tenants import seed_database
from ai_engine import (
    build_system_instruction,
    run_concierge_inference,
    ConciergeLLMResponse,
    detect_natural_instruction_mode,
    clean_reply_and_extract_components,
    auto_profile_website
)

BASE_DIR = Path(__file__).resolve().parent

# Auto-load environment variables
env_file = BASE_DIR / ".env"
env_example = BASE_DIR / ".env.example"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)
elif env_example.exists():
    load_dotenv(dotenv_path=env_example)

def get_env_var(name: str) -> str:
    val = os.getenv(name, "").strip()
    if not val:
        for p in [env_file, env_example]:
            if p.exists():
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith(f"{name}="):
                            val = line.split("=", 1)[1].strip()
                            if val:
                                return val
    return val

def check_domain_allowed(tenant: dict, request: Request) -> bool:
    """Enforces tenant-level website domain allowlist for embedded widgets."""
    allowed = tenant.get("allowed_domains") or "*"
    if allowed.strip() == "*":
        return True
    origin = request.headers.get("origin") or request.headers.get("referer") or ""
    if not origin:
        return True
    allowed_domains = [d.strip().lower() for d in allowed.split(",") if d.strip()]
    origin_lower = origin.lower()
    return any(d in origin_lower for d in allowed_domains)

# Cached persistent Gemini client
_CLIENT = None
def get_genai_client():
    global _CLIENT
    key = get_env_var("GEMINI_API_KEY")
    if not key:
        return None
    if _CLIENT is None:
        _CLIENT = genai.Client(api_key=key)
    return _CLIENT

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database and seed initial holiday clients
    default_webhook = get_env_var("GOOGLE_SHEET_WEBHOOK_URL")
    seed_database(default_webhook_url=default_webhook)
    yield

app = FastAPI(
    title="Devlancer AI – Multi-Tenant Chatbot Platform",
    version="3.0.0",
    description="Universal Multi-Tenant AI Travel Concierge & Lead Generation SaaS",
    lifespan=lifespan
)

# Enable CORS for external embeddable widgets on 3rd-party domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static directory
static_dir = BASE_DIR / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# =====================================================================
# 1. PAGE ROUTES & EMBEDDABLE ASSETS
# =====================================================================

@app.get("/")
async def root_page():
    """Serves the Devlancer Multi-Tenant Super-Admin Dashboard."""
    return FileResponse(static_dir / "admin.html")

@app.get("/admin")
async def admin_page():
    return FileResponse(static_dir / "admin.html")

@app.get("/health")
@app.get("/api/health")
async def health_check():
    """Liveness and readiness probe for Cloud platforms, Docker, and Load Balancers."""
    gemini_ready = bool(get_env_var("GEMINI_API_KEY"))
    return {
        "status": "healthy",
        "service": "Devlancer Multi-Tenant AI Platform",
        "version": "4.0.0",
        "ai_engine": "ready" if gemini_ready else "api_key_missing",
        "timestamp": time.time()
    }

@app.get("/widget.js")
async def serve_widget_script():
    """Universal script tag embedded on client websites."""
    return FileResponse(static_dir / "widget.js", media_type="application/javascript")

@app.get("/test-embed")
async def serve_test_embed_page():
    """Simulated 3rd-party customer website embedding widget.js."""
    return FileResponse(BASE_DIR / "test_embed.html")

@app.get("/demo/preview")
@app.get("/api/preview")
async def preview_any_website(request: Request, url: str = Query(...), embed: Optional[int] = Query(0)):
    """
    Renders ANY website in the world (e.g. cricbuzz.com, nike.com, stripe.com) live,
    stripping X-Frame-Options restrictions, and injecting the autonomous chameleon AI widget.
    """
    target = url.strip()
    if not target.startswith("http://") and not target.startswith("https://"):
        target = f"https://{target}"

    try:
        from urllib.parse import urlparse
        import re
        from fastapi.responses import HTMLResponse
        
        parsed = urlparse(target)
        domain = parsed.hostname or ""
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        server_base = str(request.base_url).rstrip('/')

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

        async with httpx.AsyncClient(follow_redirects=True, timeout=12.0) as http_client:
            resp = await http_client.get(target, headers=headers)
            content = resp.text

        # Strip any inline meta tags enforcing framing restrictions
        content = re.sub(r'<meta[^>]*http-equiv=["\']?X-Frame-Options["\']?[^>]*>', '', content, flags=re.I)
        content = re.sub(r'<meta[^>]*http-equiv=["\']?Content-Security-Policy["\']?[^>]*>', '', content, flags=re.I)

        # Inject <base href="..."> so all stylesheets, images, scripts, and fonts resolve cleanly
        base_tag = f'<base href="{base_url}/">'

        if "<head" in content.lower():
            content = re.sub(r'(<head[^>]*>)', r'\1' + base_tag, content, count=1, flags=re.I)
        else:
            content = base_tag + content

        # Only inject the standalone widget if not embedded in the presenter demo (to avoid duplicate overlay)
        if not embed:
            widget_script = f'<script src="{server_base}/widget.js" data-auto="true" data-domain="{domain}" defer></script>'
            if "</body" in content.lower():
                content = re.sub(r'(</body[^>]*>)', widget_script + r'\1', content, count=1, flags=re.I)
            else:
                content += widget_script

        response = HTMLResponse(content=content, status_code=200)
        response.headers["X-Frame-Options"] = "ALLOWALL"
        response.headers["Content-Security-Policy"] = "frame-ancestors *"
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response

    except Exception as e:
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=f"<div style='font-family:sans-serif;padding:32px;color:#71717a;'><h3>Unable to preview {url}</h3><p>{e}</p></div>", status_code=200)

@app.get("/demo/{slug}")
async def serve_demo_pitch_overlay(slug: str):
    """Executive split-screen pitch demo overlaying client's live website."""
    tenant = get_tenant_by_slug(slug)
    if not tenant:
        raise HTTPException(status_code=404, detail="Client agency not found")
    return FileResponse(static_dir / "demo.html")

@app.get("/c/{slug}")
async def serve_standalone_chat(slug: str):
    """Hosted standalone white-label chat page for a client."""
    tenant = get_tenant_by_slug(slug)
    if not tenant:
        raise HTTPException(status_code=404, detail="Client agency not found")
    return FileResponse(static_dir / "standalone.html")

# =====================================================================
# 2. WIDGET PUBLIC CONFIG API (Called by widget.js on 3rd-party sites)
# =====================================================================

def resolve_tenant_logo(tenant: Optional[Dict[str, Any]]) -> str:
    """Returns official logo_url, or auto-derives high-res favicon/logo from website_url."""
    if not tenant:
        return ""
    logo = (tenant.get("logo_url") or "").strip()
    web = (tenant.get("website_url") or "").strip()

    domain_clean = ""
    if web:
        try:
            from urllib.parse import urlparse
            p = urlparse(web if "://" in web else f"https://{web}")
            domain = p.hostname or p.netloc or ""
            domain_clean = domain[4:] if domain.startswith("www.") else domain
        except Exception:
            domain_clean = ""

    # If tenant has custom uploaded/configured logo (and not dummy placeholder), prioritize it
    is_dummy_placeholder = False
    if web and logo:
        normalized_web = web.rstrip("/")
        if logo.rstrip("/") == f"{normalized_web}/logo.png":
            is_dummy_placeholder = True

    if logo and not is_dummy_placeholder:
        return logo
    if domain_clean:
        return f"https://www.google.com/s2/favicons?domain={domain_clean}&sz=128"
    return logo or ""

@app.get("/api/widget/config")
async def get_widget_config(
    request: Request,
    assistant_id: Optional[str] = Query(None),
    tenant_slug: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
    origin: Optional[str] = Query(None),
    title: Optional[str] = Query(None),
    meta_desc: Optional[str] = Query(None),
    theme_color: Optional[str] = Query(None),
    site_name: Optional[str] = Query(None),
    sample_text: Optional[str] = Query(None)
):
    """Returns safe public branding & configuration for the embedded widget with autonomous domain inheritance."""
    tenant = None

    # 1. Direct identifier lookup if provided (unless explicitly 'auto')
    if assistant_id and assistant_id not in ["auto", "default"]:
        tenant = get_tenant_by_assistant_id(assistant_id)
    if not tenant and tenant_slug and tenant_slug not in ["auto", "default"]:
        tenant = get_tenant_by_slug(tenant_slug)
    if not tenant and tenant_id:
        tenant = get_tenant_by_id(tenant_id)

    # 2. Extract host domain from query or request headers
    raw_domain = domain or ""
    if not raw_domain:
        header_origin = origin or request.headers.get("origin") or request.headers.get("referer") or ""
        if header_origin:
            try:
                from urllib.parse import urlparse
                raw_domain = urlparse(header_origin).hostname or ""
            except Exception:
                raw_domain = ""

    clean_domain = raw_domain.lower().replace("www.", "").strip() if raw_domain else ""
    is_localhost = clean_domain in ["localhost", "127.0.0.1", "0.0.0.0", ""]

    # 3. Domain-based lookup in existing database
    if not tenant and clean_domain and not is_localhost:
        tenant = get_tenant_by_domain(clean_domain)

    # 4. Autonomous Profile Generation for ANY new website in the world!
    if not tenant and clean_domain and not is_localhost:
        try:
            client = get_genai_client()
            profile = await auto_profile_website(
                client=client,
                domain=clean_domain,
                page_title=title or "",
                meta_description=meta_desc or "",
                theme_color=theme_color or "",
                page_sample=sample_text or ""
            )

            new_slug = clean_domain.replace(".", "-")
            new_id = f"tenant_{clean_domain.replace('.', '_')}"
            new_asst_id = f"asst_{clean_domain.replace('.', '_')}"

            dynamic_tenant = {
                "id": new_id,
                "slug": new_slug,
                "assistant_id": new_asst_id,
                "name": profile.get("name", site_name or clean_domain.capitalize()),
                "tagline": profile.get("tagline", f"Official AI for {clean_domain}"),
                "category": profile.get("category", "general"),
                "domain": clean_domain,
                "is_dynamic": 1,
                "logo_url": f"https://www.google.com/s2/favicons?domain={clean_domain}&sz=128",
                "website_url": f"https://{clean_domain}",
                "primary_color": profile.get("primary_color", theme_color or "#0284c7"),
                "secondary_color": profile.get("secondary_color", "#0369a1"),
                "accent_color": profile.get("accent_color", "#f59e0b"),
                "assistant_name": profile.get("assistant_name", f"{clean_domain.capitalize()} AI"),
                "welcome_message": profile.get("welcome_message", f"Welcome to {clean_domain}! How can I help you today?"),
                "personality_prompt": profile.get("personality_prompt", ""),
                "knowledge_base": profile.get("knowledge_base", ""),
                "supported_languages": "English, Hindi, International",
                "contact_phone": "",
                "contact_email": f"support@{clean_domain}",
                "contact_address": f"Official Online Platform ({clean_domain})",
                "webhook_url": "",
                "allowed_domains": "*",
                "is_active": 1,
                "default_detail_level": "standard",
                "starter_prompts": json.dumps(profile.get("starter_prompts", ["Overview", "Contact Support", "Learn More"])),
                "tone_of_voice": "Helpful, authoritative, polite, and domain expert",
                "enabled_components": '["summary", "cards", "comparison_table", "steps", "accordions", "follow_up", "suggested_actions"]'
            }
            upsert_tenant(dynamic_tenant)
            tenant = dynamic_tenant
        except Exception as auto_err:
            print(f"[WARN] Failed to auto-profile domain {clean_domain}: {auto_err}")

    # Fallback to default tenant if still none
    if not tenant:
        tenants = list_all_tenants()
        tenant = tenants[0] if tenants else None

    if not tenant:
        raise HTTPException(status_code=404, detail="Assistant not found")

    # Domain allowlist check
    if not check_domain_allowed(tenant, request):
        raise HTTPException(
            status_code=403, 
            detail=f"Domain origin not authorized for this chatbot. Allowed: {tenant.get('allowed_domains')}"
        )

    packages = get_tenant_packages(tenant["id"])
    category = tenant.get("category", "travel")
    has_packages = len(packages) > 0 and category == "travel"

    perms = {}
    try:
        perms = json.loads(tenant.get("feature_permissions") or "{}")
    except Exception:
        perms = {"voice": True, "calculator": True, "export": True}

    resolved_logo = resolve_tenant_logo(tenant)

    return {
        "tenant_id": tenant["id"],
        "assistant_id": tenant["assistant_id"],
        "slug": tenant["slug"],
        "name": tenant["name"],
        "category": category,
        "domain": tenant.get("domain", ""),
        "has_packages": has_packages,
        "assistant_name": tenant["assistant_name"],
        "tagline": tenant["tagline"],
        "logo_url": resolved_logo,
        "primary_color": tenant["primary_color"],
        "secondary_color": tenant["secondary_color"],
        "accent_color": tenant["accent_color"],
        "welcome_message": tenant["welcome_message"],
        "supported_languages": tenant["supported_languages"],
        "contact_phone": tenant["contact_phone"],
        "contact_email": tenant.get("contact_email", ""),
        "contact_address": tenant.get("contact_address", ""),
        "website_url": tenant["website_url"],
        "installation_verified": bool(tenant.get("installation_verified", 0)),
        "feature_permissions": perms,
        "packages": packages,
        "default_detail_level": tenant.get("default_detail_level") or "standard",
        "starter_prompts": json.loads(tenant.get("starter_prompts") or "[]") if isinstance(tenant.get("starter_prompts"), str) else (tenant.get("starter_prompts") or []),
        "tone_of_voice": tenant.get("tone_of_voice") or "Professional, warm, and expert travel consultant",
        "enabled_components": json.loads(tenant.get("enabled_components") or "[]") if isinstance(tenant.get("enabled_components"), str) else (tenant.get("enabled_components") or ["summary", "cards", "comparison_table", "itinerary", "steps", "accordions", "checklists", "budget_breakdown", "source_references", "follow_up", "suggested_actions"])
    }

# =====================================================================
# 3. MULTI-TENANT CHAT & INFERENCE ENDPOINT
# =====================================================================

class ChatRequest(BaseModel):
    message: str
    session_id: str
    assistant_id: Optional[str] = None
    tenant_slug: Optional[str] = None
    tenant_id: Optional[str] = None
    domain: Optional[str] = None
    page_context: Optional[str] = None
    detail_mode: Optional[str] = "standard"  # "quick", "standard", "detailed"
    mode: Optional[str] = None               # "senior", "itinerary", "budget", "quick"
    action: Optional[Dict[str, Any]] = None  # Executed action payload
    history: Optional[List[Dict[str, str]]] = None # In-memory stateless client history

async def fire_webhook_background(webhook_url: str, payload: dict):
    """Asynchronously syncs lead data to Google Sheets / CRM in background."""
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as http_client:
            resp = await http_client.post(webhook_url, json=payload)
            print(f"[WEBHOOK SYNC] Lead sent to {webhook_url[:35]}... status={resp.status_code}")
    except Exception as e:
        print(f"[WARN Webhook Sync] {e}")

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest, request: Request):
    client = get_genai_client()
    if not client:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY is missing. Export it in your terminal or .env file."
        )

    # Resolve Tenant
    tenant = None
    if req.assistant_id and req.assistant_id not in ["auto", "default"]:
        tenant = get_tenant_by_assistant_id(req.assistant_id)
    if not tenant and req.tenant_slug and req.tenant_slug not in ["auto", "default"]:
        tenant = get_tenant_by_slug(req.tenant_slug)
    if not tenant and req.tenant_id:
        tenant = get_tenant_by_id(req.tenant_id)
    if not tenant and req.domain:
        tenant = get_tenant_by_domain(req.domain)
    if not tenant:
        header_origin = request.headers.get("origin") or request.headers.get("referer") or ""
        if header_origin:
            try:
                from urllib.parse import urlparse
                host = urlparse(header_origin).hostname or ""
                if host and host not in ["localhost", "127.0.0.1", "0.0.0.0"]:
                    tenant = get_tenant_by_domain(host)
            except Exception:
                pass
    if not tenant:
        # Default to Prakruthi Holidays
        tenant = get_tenant_by_slug("prakruthi-holidays")

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant agency not found")

    if tenant.get("is_active") == 0:
        raise HTTPException(status_code=403, detail="This agency chatbot is currently inactive or suspended.")

    if not check_domain_allowed(tenant, request):
        raise HTTPException(status_code=403, detail="Origin domain not allowed for this agency chatbot.")

    tenant_id = tenant["id"]
    packages = get_tenant_packages(tenant_id)

    # Client storage preference: 1 = Save full chat transcripts in DB, 0 = Zero chat storage (stateless)
    store_chat_history = int(tenant.get("store_chat_history") or 0)

    # In-memory session context
    session_context = get_session_context(tenant_id, req.session_id) if store_chat_history else {}
    
    # Resolve active detail mode (Quick / Standard / Detailed)
    active_detail = req.detail_mode or session_context.get("detail_mode") or tenant.get("default_detail_level") or "standard"
    active_detail = detect_natural_instruction_mode(req.message, active_detail)

    # Build dynamically grounded system instruction
    system_instruction = build_system_instruction(
        tenant=tenant,
        packages=packages,
        session_context=session_context,
        detail_mode=active_detail
    )

    # Conversation history: prioritize client payload, fallback to DB if store_chat_history is enabled
    if req.history:
        history = req.history[-4:]
    elif store_chat_history:
        history = get_conversation_history(tenant_id, req.session_id, limit=4)
    else:
        history = []

    try:
        # Run AI inference with structured component schema
        parsed: ConciergeLLMResponse = await run_concierge_inference(
            client=client,
            system_instruction=system_instruction,
            conversation_history=history,
            user_message=req.message,
            detail_mode=active_detail,
            mode=req.mode
        )

        # Guarantee no raw JSON leaked into human response text
        clean_reply, extra_json = clean_reply_and_extract_components(parsed.reply_message)
        if clean_reply:
            parsed.reply_message = clean_reply
        if extra_json and not parsed.cards and extra_json.get("cards"):
            try:
                from ai_engine import InfoCard
                parsed.cards = [InfoCard(**c) for c in extra_json["cards"]]
            except Exception:
                pass

        # Conditional Chat Turn Archiving (Client-controlled option)
        if store_chat_history:
            save_turn(tenant_id, req.session_id, req.message, parsed.reply_message)
            session_context["last_user_message"] = req.message
            session_context["last_model_message"] = parsed.reply_message
            session_context["detail_mode"] = active_detail
            if parsed.destination_interest:
                session_context["destination_interest"] = parsed.destination_interest
            if parsed.budget_estimate:
                session_context["budget_preference"] = parsed.budget_estimate
            upsert_session_context(tenant_id, req.session_id, session_context)

        # Log unanswered question if clarification or missing knowledge
        reply_lower = parsed.reply_message.lower()
        if (
            parsed.format_style in ["clarification", "unanswered"] or
            any(w in reply_lower for w in ["do not offer", "cannot provide", "not available", "could not find", "travel desk can verify", "outside", "don't offer", "not in our packages", "not included"])
        ):
            log_unanswered_question(
                tenant_id=tenant_id,
                session_id=req.session_id,
                question=req.message,
                reason="Flagged as missing knowledge or service clarification"
            )

        # Structure lead state
        lead_state = {
            "customer_name": parsed.customer_name or session_context.get("collected_details", {}).get("name") or None,
            "phone_number": parsed.phone_number or session_context.get("collected_details", {}).get("phone") or None,
            "destination_interest": parsed.destination_interest or session_context.get("destination_interest") or None,
            "travel_type": parsed.travel_type or session_context.get("travel_type") or None,
            "pax_count": parsed.pax_count or session_context.get("pax_count") or None,
            "budget_estimate": parsed.budget_estimate or session_context.get("budget_preference") or None,
            "travel_month": parsed.travel_month or session_context.get("travel_month") or None,
            "includes_seniors": parsed.includes_seniors or session_context.get("includes_seniors", False),
            "lead_score": parsed.lead_score or ("HOT" if parsed.phone_number else "COLD"),
            "summary_notes": parsed.summary_notes or f"Inquiry regarding {parsed.destination_interest or 'offerings'}"
        }

        crm_synced_now = False
        phone = (parsed.phone_number or "").strip()

        # HIGH-INTENT LEAD & OPPORTUNITY CAPTURE
        # Always store leads in the CRM, even when chat storage is disabled!
        # Leads must NEVER be lost.
        msg_lower = req.message.lower()
        is_buying_intent = (
            bool(parsed.destination_interest) or 
            bool(parsed.budget_estimate) or 
            parsed.lead_score in ["HOT", "WARM"] or
            any(k in msg_lower for k in ["book", "buy", "price", "pricing", "quote", "cost", "reserve", "order", "purchase", "callback", "contact me", "hire", "deal", "how much", "pay", "interested in"])
        )

        if phone or is_buying_intent:
            contact_label = phone if phone else "Website Visitor (Pending Contact)"
            score_label = "HOT 🔥" if phone else "INQUIRY 🎯"
            
            inquiry_target = (
                lead_state["destination_interest"] or 
                (req.message[:50].strip() if len(req.message) > 5 else "Product / Package Inquiry")
            )

            lead_payload = {
                "tenant_id": tenant_id,
                "session_id": req.session_id,
                "customer_name": lead_state["customer_name"] or "Website Visitor",
                "phone_number": contact_label,
                "destination": inquiry_target,
                "travel_type": lead_state["travel_type"] or "General Inquiry",
                "pax_count": lead_state["pax_count"] or "TBD",
                "budget": lead_state["budget_estimate"] or "Standard",
                "travel_month": lead_state["travel_month"] or "Flexible",
                "includes_seniors": "YES (Priority)" if lead_state["includes_seniors"] else "No",
                "lead_score": score_label,
                "summary_notes": lead_state["summary_notes"] or f"Inquiry: {req.message[:120]}"
            }

            insert_lead(lead_payload)
            crm_synced_now = True

            webhook_url = tenant.get("webhook_url") or get_env_var("GOOGLE_SHEET_WEBHOOK_URL")
            if webhook_url:
                lead_webhook_data = {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "agency_name": tenant["name"],
                    **lead_payload
                }
                asyncio.create_task(fire_webhook_background(webhook_url, lead_webhook_data))

        comp_table = None
        if parsed.comparison_table:
            comp_table = {
                "title": parsed.comparison_table.title,
                "headers": parsed.comparison_table.headers,
                "rows": [r.cells if hasattr(r, 'cells') else (r.get('cells') if isinstance(r, dict) else r) for r in parsed.comparison_table.rows],
                "highlights": parsed.comparison_table.highlights
            }

        follow_up_data = None
        if parsed.follow_up:
            follow_up_data = {
                "question": parsed.follow_up.question,
                "field_needed": parsed.follow_up.field_needed,
                "chips": parsed.follow_up.chips,
                "options": parsed.follow_up.chips
            }

        # Build clean components payload for frontend response renderer
        components = {
            "summary": parsed.summary,
            "cards": [c.model_dump() for c in parsed.cards] if parsed.cards else [],
            "comparison_table": comp_table,
            "itinerary": [d.model_dump() for d in parsed.itinerary] if parsed.itinerary else [],
            "steps": [s.model_dump() for s in parsed.steps] if parsed.steps else [],
            "accordions": [a.model_dump() for a in parsed.accordions] if parsed.accordions else [],
            "checklists": [c.model_dump() for c in parsed.checklists] if parsed.checklists else [],
            "budget_breakdown": parsed.budget_breakdown.model_dump() if parsed.budget_breakdown else None,
            "source_references": [sr.model_dump() for sr in parsed.source_references] if parsed.source_references else [],
            "follow_up": follow_up_data,
            "suggested_actions": [sa.model_dump() for sa in parsed.suggested_actions] if parsed.suggested_actions else []
        }

        total_leads_count = count_tenant_leads(tenant_id=tenant_id)

        return {
            "reply": parsed.reply_message,
            "reply_message": parsed.reply_message,
            "summary": parsed.summary,
            "format_style": parsed.format_style,
            "detail_mode": active_detail,
            "components": components,
            "quick_replies": parsed.suggested_quick_replies,
            "suggested_actions": components["suggested_actions"],
            "lead_state": lead_state,
            "crm_synced_now": crm_synced_now,
            "total_leads_captured": total_leads_count
        }

    except Exception as e:
        print(f"[ERROR /api/chat] {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================================
# 4. TENANT ONBOARDING & MANAGEMENT APIS
# =====================================================================

def classify_business_category(name: str, website_url: str, knowledge_base: str = "", welcome: str = "") -> str:
    """Intelligently detects domain category to avoid wrong travel defaults."""
    combined = f"{name} {website_url} {knowledge_base} {welcome}".lower()
    if any(k in combined for k in ["movie", "film", "cinema", "imdb", "series", "actor", "hollywood", "bollywood", "rating"]):
        return "entertainment_movies"
    if any(k in combined for k in ["cricket", "cricbuzz", "ipl", "match score", "t20", "icc", "wicket", "batsman"]):
        return "sports_cricket"
    if any(k in combined for k in ["football", "soccer", "basketball", "nba", "fifa", "sports"]):
        return "sports"
    if any(k in combined for k in ["shoe", "sneaker", "apparel", "clothing", "ecommerce", "store", "cart", "shop", "fashion"]):
        return "ecommerce"
    if any(k in combined for k in ["saas", "software", "api", "cloud", "developer", "platform", "billing", "stripe"]):
        return "tech_saas"
    if any(k in combined for k in ["travel", "holiday", "tour", "trip", "resort", "hotel", "flight", "safari", "vacation", "itinerary"]):
        return "travel"
    return "general"

class CreateTenantRequest(BaseModel):
    name: str
    slug: str
    website_url: str
    category: Optional[str] = None
    tagline: Optional[str] = ""
    logo_url: Optional[str] = ""
    assistant_name: Optional[str] = None
    primary_color: Optional[str] = "#047857"
    secondary_color: Optional[str] = "#064e3b"
    accent_color: Optional[str] = "#f59e0b"
    welcome_message: str
    personality_prompt: Optional[str] = ""
    knowledge_base: str
    supported_languages: Optional[str] = "English, Hindi"
    contact_phone: Optional[str] = ""
    contact_email: Optional[str] = ""
    contact_address: Optional[str] = ""
    webhook_url: Optional[str] = ""
    default_detail_level: Optional[str] = "standard"
    tone_of_voice: Optional[str] = None
    starter_prompts: Optional[str] = "[]"
    enabled_components: Optional[str] = '["summary", "cards", "comparison_table", "itinerary", "steps", "accordions", "checklists", "budget_breakdown", "source_references", "follow_up", "suggested_actions"]'
    store_chat_history: Optional[int] = 0

@app.get("/api/tenants")
async def api_list_tenants():
    tenants = list_all_tenants()
    for t in tenants:
        t["logo_url"] = resolve_tenant_logo(t)
    return tenants

@app.post("/api/tenants")
async def api_create_tenant(req: CreateTenantRequest):
    # Check if slug exists
    existing = get_tenant_by_slug(req.slug)
    if existing:
        raise HTTPException(status_code=400, detail="An agency with this slug already exists.")

    tenant_id = f"tenant_{int(time.time()*1000)}"
    assistant_id = f"asst_{req.slug.replace('-', '_')}"

    logo_resolved = (req.logo_url or "").strip()
    if not logo_resolved:
        logo_resolved = resolve_tenant_logo({"website_url": req.website_url, "logo_url": ""})

    # Classify business category accurately
    category = req.category or classify_business_category(req.name, req.website_url, req.knowledge_base, req.welcome_message)
    domain_clean = ""
    if req.website_url:
        try:
            from urllib.parse import urlparse
            p = urlparse(req.website_url if "://" in req.website_url else f"https://{req.website_url}")
            domain_clean = (p.hostname or "").lower().replace("www.", "")
        except Exception:
            domain_clean = ""

    default_asst_name = req.assistant_name or (f"{req.name} Assistant" if category != "travel" else "Travel Concierge AI")
    default_tagline = req.tagline or (f"Official AI Concierge for {req.name}" if category != "travel" else f"Premium Travel Services by {req.name}")
    default_tone = req.tone_of_voice or (f"Helpful, knowledgeable, and domain expert for {req.name}" if category != "travel" else "Professional, warm, and expert travel consultant")
    default_personality = req.personality_prompt or f"You are the official AI concierge for {req.name}."

    tenant_data = {
        "id": tenant_id,
        "slug": req.slug,
        "assistant_id": assistant_id,
        "name": req.name,
        "category": category,
        "domain": domain_clean,
        "tagline": default_tagline,
        "logo_url": logo_resolved,
        "website_url": req.website_url,
        "primary_color": req.primary_color,
        "secondary_color": req.secondary_color,
        "accent_color": req.accent_color,
        "assistant_name": default_asst_name,
        "welcome_message": req.welcome_message,
        "personality_prompt": default_personality,
        "knowledge_base": req.knowledge_base,
        "supported_languages": req.supported_languages,
        "contact_phone": req.contact_phone,
        "contact_email": req.contact_email,
        "contact_address": req.contact_address,
        "webhook_url": req.webhook_url,
        "allowed_domains": "*",
        "is_active": 1,
        "default_detail_level": req.default_detail_level or "standard",
        "tone_of_voice": default_tone,
        "starter_prompts": req.starter_prompts or "[]",
        "enabled_components": req.enabled_components or '["summary", "cards", "comparison_table", "itinerary", "steps", "accordions", "checklists", "budget_breakdown", "source_references", "follow_up", "suggested_actions"]',
        "store_chat_history": int(req.store_chat_history or 0)
    }

    upsert_tenant(tenant_data)

    # Seed default starter package ONLY IF the tenant is an actual travel agency!
    if category == "travel":
        set_tenant_packages(tenant_id, [
            {
                "name": "Featured International Tour",
                "destination": "International",
                "duration": "5 Nights / 6 Days",
                "starting_price_inr": 85000,
                "highlights": "Comprehensive sightseeing, curated hotels, and guided support."
            }
        ])
    else:
        set_tenant_packages(tenant_id, [])

    return {
        "status": "success",
        "message": f"Successfully onboarded {req.name}!",
        "tenant_id": tenant_id,
        "assistant_id": assistant_id,
        "category": category,
        "embed_snippet": f'<script src="/widget.js" data-assistant-id="{assistant_id}" defer></script>'
    }

@app.get("/api/tenants/{slug_or_id}")
async def api_get_tenant(slug_or_id: str):
    tenant = get_tenant_by_slug(slug_or_id) or get_tenant_by_id(slug_or_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    tenant["logo_url"] = resolve_tenant_logo(tenant)
    packages = get_tenant_packages(tenant["id"])
    return {"tenant": tenant, "packages": packages}

@app.put("/api/tenants/{tenant_id}")
async def api_update_tenant(tenant_id: str, updates: Dict[str, Any]):
    tenant = get_tenant_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    success = update_tenant_settings(tenant_id, updates)
    return {"status": "success" if success else "no_changes", "tenant_id": tenant_id}

@app.delete("/api/tenants/{tenant_id}")
async def api_delete_tenant(tenant_id: str):
    success = delete_tenant(tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"status": "success", "message": "Tenant deleted"}

class VerifyInstallRequest(BaseModel):
    tenant_id: Optional[str] = None
    slug: Optional[str] = None
    assistant_id: Optional[str] = None

@app.post("/api/verify-install")
async def api_verify_install(req: VerifyInstallRequest):
    """
    Real crawler verification workflow.
    Inspects client website HTML for presence of the widget script and matching data-assistant-id.
    Never claims installation is verified unless real verification succeeded.
    """
    tenant = None
    if req.tenant_id:
        tenant = get_tenant_by_id(req.tenant_id)
    elif req.slug:
        tenant = get_tenant_by_slug(req.slug)
    elif req.assistant_id:
        tenant = get_tenant_by_assistant_id(req.assistant_id)
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Agency tenant not found")

    target_url = (tenant.get("website_url") or "").strip()
    if not target_url or not target_url.startswith("http"):
        return {
            "verified": False,
            "message": "Invalid or missing website URL configured for this agency.",
            "diagnostics": {"website_url": target_url}
        }

    assistant_id = tenant["assistant_id"]
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 DevlancerWidgetBot/3.0"
        }
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, verify=False) as client:
            resp = await client.get(target_url, headers=headers)
            body = resp.text

            has_script = "widget.js" in body
            has_asst = assistant_id in body

            if has_script and has_asst:
                verify_tenant_installation(tenant["id"], True)
                return {
                    "verified": True,
                    "message": f"Installation verified! Embed script with assistant ID '{assistant_id}' is active on {target_url}.",
                    "diagnostics": {
                        "status_code": resp.status_code,
                        "script_found": True,
                        "assistant_id_found": True,
                        "checked_url": str(resp.url)
                    }
                }
            else:
                verify_tenant_installation(tenant["id"], False)
                return {
                    "verified": False,
                    "message": f"Script not detected on {target_url}. Please ensure the embed snippet is pasted before </body> or inside <head>.",
                    "diagnostics": {
                        "status_code": resp.status_code,
                        "script_found": has_script,
                        "assistant_id_found": has_asst,
                        "expected_assistant_id": assistant_id,
                        "troubleshooting": f"Add '<script src=\"/widget.js\" data-assistant-id=\"{assistant_id}\" defer></script>' to {target_url} and click Verify again."
                    }
                }
    except Exception as e:
        verify_tenant_installation(tenant["id"], False)
        return {
            "verified": False,
            "message": f"Could not reach {target_url}: {str(e)}",
            "diagnostics": {"error": str(e), "troubleshooting": "Verify domain is accessible publicly and DNS is resolved."}
        }

# =====================================================================
# 5. UNIFIED LEADS & CRM APIS
# =====================================================================

@app.get("/api/leads")
async def api_get_leads(
    tenant_slug: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None)
):
    target_id = None
    if tenant_slug:
        t = get_tenant_by_slug(tenant_slug)
        if t: target_id = t["id"]
    elif tenant_id:
        target_id = tenant_id

    leads = list_tenant_leads(tenant_id=target_id, limit=200)
    return {
        "webhook_configured": bool(get_env_var("GOOGLE_SHEET_WEBHOOK_URL")),
        "leads": leads
    }

@app.delete("/api/leads/{lead_id}")
async def api_delete_lead(lead_id: str):
    success = delete_lead(lead_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"status": "success", "message": "Lead deleted"}

@app.get("/api/admin/conversations")
async def api_get_conversations(
    tenant_slug: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
    limit: int = Query(50)
):
    """Retrieves stored conversation threads and transcripts across all tenants."""
    target_id = None
    if tenant_slug:
        t = get_tenant_by_slug(tenant_slug)
        if t: target_id = t["id"]
    elif tenant_id:
        target_id = tenant_id

    convs = list_tenant_conversations(target_id, limit=limit)
    return {
        "total_conversations": len(convs),
        "conversations": convs
    }

@app.get("/api/admin/conversations/{conversation_id}/messages")
async def api_get_conversation_messages(conversation_id: str):
    """Retrieves full transcript messages (user turns and AI replies) for a conversation."""
    msgs = get_conversation_messages(conversation_id)
    return {
        "conversation_id": conversation_id,
        "total_messages": len(msgs),
        "messages": msgs
    }

class ManualLeadInput(BaseModel):
    customer_name: str
    phone_number: str
    destination: Optional[str] = "General Inquiry"
    travel_type: Optional[str] = "Not Specified"
    pax_count: Optional[str] = "1"
    budget: Optional[str] = "Standard"
    travel_month: Optional[str] = "Flexible"
    includes_seniors: bool = False
    notes: Optional[str] = ""
    tenant_slug: Optional[str] = "prakruthi-holidays"
    assistant_id: Optional[str] = None

@app.post("/api/manual-lead")
async def api_submit_manual_lead(req: ManualLeadInput):
    tenant = None
    if req.assistant_id:
        tenant = get_tenant_by_assistant_id(req.assistant_id)
    if not tenant and req.tenant_slug:
        tenant = get_tenant_by_slug(req.tenant_slug)
    if not tenant:
        tenant = get_tenant_by_slug("prakruthi-holidays")

    tenant_id = tenant["id"] if tenant else "tenant_prakruthi"

    lead_payload = {
        "tenant_id": tenant_id,
        "customer_name": req.customer_name,
        "phone_number": req.phone_number,
        "destination": req.destination or "General Inquiry",
        "travel_type": req.travel_type or "Custom",
        "pax_count": req.pax_count or "TBD",
        "budget": req.budget or "Standard",
        "travel_month": req.travel_month or "Flexible",
        "includes_seniors": "YES (Priority)" if req.includes_seniors else "No",
        "lead_score": "HOT 🔥",
        "summary_notes": req.notes or f"Manual request for {req.destination}"
    }

    insert_lead(lead_payload)

    webhook_url = (tenant.get("webhook_url") if tenant else "") or get_env_var("GOOGLE_SHEET_WEBHOOK_URL")
    if webhook_url:
        data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "agency_name": tenant["name"] if tenant else "Prakruthi Holidays",
            **lead_payload
        }
        asyncio.create_task(fire_webhook_background(webhook_url, data))

    total = len(list_tenant_leads(tenant_id))
    return {
        "status": "success",
        "message": "Lead saved & synced!",
        "total_leads_captured": total
    }

@app.get("/api/analytics")
async def api_get_analytics():
    return get_platform_analytics()

class FeedbackRequest(BaseModel):
    session_id: str
    tenant_id: Optional[str] = None
    assistant_id: Optional[str] = None
    rating: Any = "up"  # "up", "down", 5, 4, etc.
    comment: Optional[str] = ""
    comments: Optional[str] = ""

@app.post("/api/feedback")
async def api_submit_feedback(req: FeedbackRequest):
    tenant = None
    if req.tenant_id:
        tenant = get_tenant_by_id(req.tenant_id)
    elif req.assistant_id:
        tenant = get_tenant_by_assistant_id(req.assistant_id)
    tenant_id = tenant["id"] if tenant else "tenant_prakruthi"
    comment_text = req.comment or req.comments or ""
    save_feedback(tenant_id, req.session_id, str(req.rating), comment_text)
    return {"status": "success", "message": "Feedback recorded"}

class PrivacyDeleteRequest(BaseModel):
    session_id: str
    assistant_id: Optional[str] = None
    tenant_id: Optional[str] = None

@app.post("/api/privacy/delete-session-data")
async def api_delete_session_data(req: PrivacyDeleteRequest):
    tenant = None
    if req.tenant_id:
        tenant = get_tenant_by_id(req.tenant_id)
    elif req.assistant_id:
        tenant = get_tenant_by_assistant_id(req.assistant_id)
    tenant_id = tenant["id"] if tenant else "tenant_prakruthi"
    delete_conversation_data(tenant_id, req.session_id)
    return {"status": "success", "message": "All session messages and conversation memory deleted permanently."}

@app.post("/api/clear-session")
async def api_clear_session(req: Dict[str, str]):
    return {"status": "cleared", "session_id": req.get("session_id")}

# =====================================================================
# 5. CONVERSATION ACTION ENGINE & REGENERATION
# =====================================================================

ALLOWED_ACTION_TYPES = {
    "send_message",
    "compare_packages",
    "start_itinerary",
    "request_callback",
    "submit_enquiry_confirm",
    "filter_budget",
    "open_url",
    "set_detail_mode",
    "clear_memory"
}

class ActionExecuteRequest(BaseModel):
    session_id: str
    action_type: Optional[str] = None
    action: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None
    assistant_id: Optional[str] = None
    tenant_slug: Optional[str] = None
    tenant_id: Optional[str] = None
    detail_mode: Optional[str] = "standard"

@app.post("/api/action/execute")
async def api_execute_action(req: ActionExecuteRequest, request: Request):
    """Secure Action Dispatcher: Enforces explicit allowlist and validated parameters."""
    act_type = req.action_type or req.action
    if not act_type or act_type not in ALLOWED_ACTION_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Action '{act_type}' is not recognized or authorized."
        )

    act_payload = {}
    if req.payload:
        act_payload.update(req.payload)
    if req.parameters:
        act_payload.update(req.parameters)

    # Resolve Tenant
    tenant = None
    if req.assistant_id:
        tenant = get_tenant_by_assistant_id(req.assistant_id)
    if not tenant and req.tenant_slug:
        tenant = get_tenant_by_slug(req.tenant_slug)
    if not tenant and req.tenant_id:
        tenant = get_tenant_by_id(req.tenant_id)
    if not tenant:
        tenant = get_tenant_by_slug("prakruthi-holidays")

    tenant_id = tenant["id"] if tenant else "tenant_prakruthi"

    # Action 1: Explicit Confirmation Before Submitting Personal Lead to CRM
    if act_type == "submit_enquiry_confirm":
        p = act_payload
        phone = (p.get("phone_number") or "").strip()
        if not phone:
            raise HTTPException(status_code=400, detail="Phone number is required for enquiry confirmation.")

        lead_payload = {
            "tenant_id": tenant_id,
            "session_id": req.session_id,
            "customer_name": p.get("customer_name") or "Website Visitor",
            "phone_number": phone,
            "destination": p.get("destination") or "Confirmed Package Inquiry",
            "travel_type": p.get("travel_type") or "Tour",
            "pax_count": p.get("pax_count") or "TBD",
            "budget": p.get("budget") or "Standard",
            "travel_month": p.get("travel_month") or "Flexible",
            "includes_seniors": "YES (Priority)" if p.get("includes_seniors") else "No",
            "lead_score": "HOT 🔥",
            "summary_notes": p.get("summary_notes") or p.get("notes") or f"Confirmed inquiry for {p.get('destination')}"
        }

        lead_id = insert_lead(lead_payload)

        webhook_url = (tenant.get("webhook_url") if tenant else "") or get_env_var("GOOGLE_SHEET_WEBHOOK_URL")
        if webhook_url:
            data = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "agency_name": tenant["name"] if tenant else "Holiday Agency",
                **lead_payload
            }
            asyncio.create_task(fire_webhook_background(webhook_url, data))

        return {
            "status": "success",
            "action_executed": "submit_enquiry_confirm",
            "lead_id": lead_id,
            "message": f"Thank you! Your travel request has been confirmed with {tenant['name'] if tenant else 'our team'}. We will WhatsApp your tailored itinerary shortly.",
            "crm_synced": True
        }

    # Action 2: Reset Session Context & Memory
    elif act_type == "clear_memory":
        clear_session_context(tenant_id, req.session_id)
        return {
            "status": "success",
            "action_executed": "clear_memory",
            "message": "Conversation memory reset for a fresh planning session."
        }

    # Action 3: Set Response Detail Mode
    elif act_type == "set_detail_mode":
        new_mode = act_payload.get("detail_mode", "standard")
        upsert_session_context(tenant_id, req.session_id, {"detail_mode": new_mode})
        return {
            "status": "success",
            "action_executed": "set_detail_mode",
            "detail_mode": new_mode,
            "message": f"Response preference set to '{new_mode}' mode."
        }

    # Action 4: Conversational Actions (compare, start itinerary, prompt)
    else:
        msg = act_payload.get("message")
        if not msg:
            if act_type == "compare_packages":
                pkgs = act_payload.get("packages") or "top packages"
                msg = f"Please compare these packages side-by-side in a table: {pkgs}"
            elif act_type == "start_itinerary":
                dest = act_payload.get("destination") or "this trip"
                msg = f"Create a detailed day-by-day itinerary for {dest}"
            elif act_type == "filter_budget":
                b = act_payload.get("budget") or "budget-friendly"
                msg = f"Show me options under {b}"
            elif act_type == "request_callback":
                msg = "I would like to request a callback from a travel consultant."
            else:
                msg = "Please tell me more about your packages."

        # Forward to chat endpoint
        chat_req = ChatRequest(
            message=msg,
            session_id=req.session_id,
            assistant_id=req.assistant_id,
            tenant_slug=req.tenant_slug,
            tenant_id=req.tenant_id,
            detail_mode=req.detail_mode or "standard",
            action=req.model_dump()
        )
        return await chat_endpoint(chat_req, request)

class RegenerateRequest(BaseModel):
    session_id: str
    detail_mode: str = "standard"  # "quick", "standard", "detailed"
    assistant_id: Optional[str] = None
    tenant_slug: Optional[str] = None
    tenant_id: Optional[str] = None

@app.post("/api/chat/regenerate")
async def api_regenerate_chat(req: RegenerateRequest, request: Request):
    """Regenerates the last response in a different detail mode without losing context."""
    tenant = None
    if req.assistant_id:
        tenant = get_tenant_by_assistant_id(req.assistant_id)
    if not tenant and req.tenant_slug:
        tenant = get_tenant_by_slug(req.tenant_slug)
    if not tenant and req.tenant_id:
        tenant = get_tenant_by_id(req.tenant_id)
    if not tenant:
        tenant = get_tenant_by_slug("prakruthi-holidays")

    tenant_id = tenant["id"] if tenant else "tenant_prakruthi"
    ctx = get_session_context(tenant_id, req.session_id)
    last_msg = ctx.get("last_user_message") or "Tell me about your holiday packages"

    chat_req = ChatRequest(
        message=last_msg,
        session_id=req.session_id,
        assistant_id=req.assistant_id,
        tenant_slug=req.tenant_slug,
        tenant_id=req.tenant_id,
        detail_mode=req.detail_mode
    )
    return await chat_endpoint(chat_req, request)

@app.post("/api/chat/reset")
async def api_reset_conversation(req: Dict[str, str]):
    """Completely resets session context and stored messages."""
    session_id = req.get("session_id")
    tenant_id = req.get("tenant_id") or "tenant_prakruthi"
    if session_id:
        clear_session_context(tenant_id, session_id)
        delete_conversation_data(tenant_id, session_id)
    return {"status": "success", "message": "Conversation session reset successfully."}

@app.get("/api/admin/unanswered")
async def api_get_unanswered(tenant_id: Optional[str] = None, limit: int = 50):
    """Returns recurring questions that could not be satisfied by tenant knowledge."""
    return {"unanswered_questions": list_unanswered_questions(tenant_id, limit)}

@app.get("/api/admin/feedback")
async def api_get_feedback(tenant_id: Optional[str] = None, limit: int = 50):
    """Returns customer feedback with ratings and comments."""
    return {"feedback": list_feedback(tenant_id, limit)}


