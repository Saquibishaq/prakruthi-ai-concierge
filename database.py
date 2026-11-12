"""
Devlancer Multi-Tenant Database Layer (SQLite + WAL Mode)
Provides robust tenant isolation, data persistence, and relationship integrity.
"""

import sqlite3
import json
import time
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any

BASE_DIR = Path(__file__).resolve().parent

# On Vercel / serverless runtimes, file system is read-only except /tmp
if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    DB_PATH = Path("/tmp/devlancer_platform.db")
    bundled_db = BASE_DIR / "devlancer_platform.db"
    if bundled_db.exists() and not DB_PATH.exists():
        try:
            shutil.copy2(bundled_db, DB_PATH)
        except Exception:
            pass
else:
    DB_PATH = BASE_DIR / "devlancer_platform.db"

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode = WAL;")
    except Exception:
        conn.execute("PRAGMA journal_mode = DELETE;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initializes tables, indices, and default seed data."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # 1. Tenants Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tenants (
            id TEXT PRIMARY KEY,
            slug TEXT UNIQUE NOT NULL,
            assistant_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            tagline TEXT DEFAULT '',
            logo_url TEXT DEFAULT '',
            website_url TEXT DEFAULT '',
            primary_color TEXT DEFAULT '#047857',
            secondary_color TEXT DEFAULT '#064e3b',
            accent_color TEXT DEFAULT '#f59e0b',
            assistant_name TEXT DEFAULT 'Travel Concierge AI',
            welcome_message TEXT DEFAULT '',
            personality_prompt TEXT DEFAULT '',
            knowledge_base TEXT DEFAULT '',
            supported_languages TEXT DEFAULT 'English, Kannada, Hindi',
            contact_phone TEXT DEFAULT '',
            contact_email TEXT DEFAULT '',
            contact_address TEXT DEFAULT '',
            webhook_url TEXT DEFAULT '',
            allowed_domains TEXT DEFAULT '*',
            is_active INTEGER DEFAULT 1,
            installation_verified INTEGER DEFAULT 0,
            installation_verified_at TEXT DEFAULT '',
            feature_permissions TEXT DEFAULT '{"voice": true, "calculator": true, "export": true}',
            usage_limits TEXT DEFAULT '{"monthly_chat_limit": 5000, "lead_limit": 1000}',
            subscription_status TEXT DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Migration column checks for existing SQLite databases
        cols = [r[1] for r in cursor.execute("PRAGMA table_info(tenants);").fetchall()]
        if "installation_verified" not in cols:
            cursor.execute("ALTER TABLE tenants ADD COLUMN installation_verified INTEGER DEFAULT 0;")
        if "installation_verified_at" not in cols:
            cursor.execute("ALTER TABLE tenants ADD COLUMN installation_verified_at TEXT DEFAULT '';")
        if "feature_permissions" not in cols:
            cursor.execute("ALTER TABLE tenants ADD COLUMN feature_permissions TEXT DEFAULT '{\"voice\": true, \"calculator\": true, \"export\": true}';")
        if "usage_limits" not in cols:
            cursor.execute("ALTER TABLE tenants ADD COLUMN usage_limits TEXT DEFAULT '{\"monthly_chat_limit\": 5000, \"lead_limit\": 1000}';")
        if "subscription_status" not in cols:
            cursor.execute("ALTER TABLE tenants ADD COLUMN subscription_status TEXT DEFAULT 'active';")
        if "default_detail_level" not in cols:
            cursor.execute("ALTER TABLE tenants ADD COLUMN default_detail_level TEXT DEFAULT 'standard';")
        if "starter_prompts" not in cols:
            cursor.execute("ALTER TABLE tenants ADD COLUMN starter_prompts TEXT DEFAULT '[]';")
        if "tone_of_voice" not in cols:
            cursor.execute("ALTER TABLE tenants ADD COLUMN tone_of_voice TEXT DEFAULT 'Professional, warm, and expert travel consultant';")
        if "enabled_components" not in cols:
            cursor.execute("ALTER TABLE tenants ADD COLUMN enabled_components TEXT DEFAULT '[\"summary\", \"cards\", \"comparison_table\", \"itinerary\", \"steps\", \"accordions\", \"checklists\", \"budget_breakdown\", \"source_references\", \"follow_up\", \"suggested_actions\"]';")
        if "category" not in cols:
            cursor.execute("ALTER TABLE tenants ADD COLUMN category TEXT DEFAULT 'travel';")
        if "domain" not in cols:
            cursor.execute("ALTER TABLE tenants ADD COLUMN domain TEXT DEFAULT '';")
        if "is_dynamic" not in cols:
            cursor.execute("ALTER TABLE tenants ADD COLUMN is_dynamic INTEGER DEFAULT 0;")
        if "store_chat_history" not in cols:
            cursor.execute("ALTER TABLE tenants ADD COLUMN store_chat_history INTEGER DEFAULT 0;")

        # 2. Packages Table (Tenant-isolated)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS packages (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            destination TEXT NOT NULL,
            duration TEXT NOT NULL,
            starting_price_inr INTEGER NOT NULL,
            highlights TEXT NOT NULL,
            category TEXT DEFAULT 'International Group Tour',
            is_featured INTEGER DEFAULT 1,
            FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
        );
        """)

        # 3. Conversations Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
            UNIQUE(tenant_id, session_id)
        );
        """)

        # 4. Messages Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            tenant_id TEXT NOT NULL,
            role TEXT NOT NULL,
            text TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
            FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
        );
        """)

        # 5. Leads Table (Tenant-isolated)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            session_id TEXT DEFAULT '',
            customer_name TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            destination TEXT DEFAULT 'General Inquiry',
            travel_type TEXT DEFAULT 'Not Specified',
            pax_count TEXT DEFAULT 'TBD',
            budget TEXT DEFAULT 'Standard',
            travel_month TEXT DEFAULT 'Flexible',
            includes_seniors TEXT DEFAULT 'No',
            lead_score TEXT DEFAULT 'HOT 🔥',
            summary_notes TEXT DEFAULT '',
            synced_to_webhook INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
        );
        """)

        # 6. Feedback Table (User response ratings)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            rating TEXT NOT NULL,
            comment TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
        );
        """)

        # 7. Session Contexts Table (Structured Cross-turn Memory)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_contexts (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            user_objective TEXT DEFAULT '',
            destination_interest TEXT DEFAULT '',
            budget_preference TEXT DEFAULT '',
            pax_count TEXT DEFAULT '',
            travel_month TEXT DEFAULT '',
            travel_type TEXT DEFAULT '',
            includes_seniors INTEGER DEFAULT 0,
            options_discussed TEXT DEFAULT '[]',
            collected_details TEXT DEFAULT '{}',
            unanswered_questions TEXT DEFAULT '[]',
            detail_mode TEXT DEFAULT 'standard',
            last_user_message TEXT DEFAULT '',
            last_model_message TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
            UNIQUE(tenant_id, session_id)
        );
        """)

        # 8. Unanswered Questions Table (Missing KB / Escalation tracking)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS unanswered_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            question TEXT NOT NULL,
            reason TEXT DEFAULT 'Information not found in tenant knowledge base',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
        );
        """)

        # Indices for high-concurrency read queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tenants_slug ON tenants(slug);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tenants_assistant ON tenants(assistant_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_packages_tenant ON packages(tenant_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_tenant ON conversations(tenant_id, session_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_tenant ON leads(tenant_id, created_at);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_contexts_tenant ON session_contexts(tenant_id, session_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_unanswered_tenant ON unanswered_questions(tenant_id, created_at);")

        conn.commit()

# --- Tenant CRUD Helpers ---

def get_tenant_by_id(tenant_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM tenants WHERE id = ?;", (tenant_id,)).fetchone()
        return dict(row) if row else None

def get_tenant_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM tenants WHERE slug = ?;", (slug,)).fetchone()
        return dict(row) if row else None

def get_tenant_by_assistant_id(assistant_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM tenants WHERE assistant_id = ? AND is_active = 1;", (assistant_id,)).fetchone()
        return dict(row) if row else None

def list_all_tenants() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT t.*, 
                   (SELECT COUNT(*) FROM leads l WHERE l.tenant_id = t.id) AS total_leads,
                   (SELECT COUNT(*) FROM conversations c WHERE c.tenant_id = t.id) AS total_conversations
            FROM tenants t 
            ORDER BY t.created_at ASC;
        """).fetchall()
        return [dict(r) for r in rows]

def upsert_tenant(tenant: Dict[str, Any]) -> str:
    # Ensure default values for all supported columns
    t = {
        "id": tenant["id"],
        "slug": tenant.get("slug", ""),
        "assistant_id": tenant.get("assistant_id", ""),
        "name": tenant.get("name", ""),
        "tagline": tenant.get("tagline", ""),
        "category": tenant.get("category", "travel"),
        "domain": tenant.get("domain", ""),
        "is_dynamic": tenant.get("is_dynamic", 0),
        "logo_url": tenant.get("logo_url", ""),
        "website_url": tenant.get("website_url", ""),
        "primary_color": tenant.get("primary_color", "#047857"),
        "secondary_color": tenant.get("secondary_color", "#064e3b"),
        "accent_color": tenant.get("accent_color", "#f59e0b"),
        "assistant_name": tenant.get("assistant_name", "Travel Concierge AI"),
        "welcome_message": tenant.get("welcome_message", "Hello! How can I assist with your journey?"),
        "personality_prompt": tenant.get("personality_prompt", ""),
        "knowledge_base": tenant.get("knowledge_base", ""),
        "supported_languages": tenant.get("supported_languages", "English, Hindi"),
        "contact_phone": tenant.get("contact_phone", ""),
        "contact_email": tenant.get("contact_email", ""),
        "contact_address": tenant.get("contact_address", ""),
        "webhook_url": tenant.get("webhook_url", ""),
        "allowed_domains": tenant.get("allowed_domains", "*"),
        "is_active": tenant.get("is_active", 1),
        "default_detail_level": tenant.get("default_detail_level", "standard"),
        "starter_prompts": tenant.get("starter_prompts", "[]"),
        "tone_of_voice": tenant.get("tone_of_voice", "Professional, warm, and expert travel consultant"),
        "enabled_components": tenant.get("enabled_components", '["summary", "cards", "comparison_table", "itinerary", "steps", "accordions", "checklists", "budget_breakdown", "source_references", "follow_up", "suggested_actions"]'),
        "store_chat_history": tenant.get("store_chat_history", 0)
    }
    with get_connection() as conn:
        conn.execute("""
        INSERT INTO tenants (
            id, slug, assistant_id, name, tagline, category, domain, is_dynamic, logo_url, website_url,
            primary_color, secondary_color, accent_color, assistant_name,
            welcome_message, personality_prompt, knowledge_base,
            supported_languages, contact_phone, contact_email, contact_address,
            webhook_url, allowed_domains, is_active,
            default_detail_level, starter_prompts, tone_of_voice, enabled_components,
            store_chat_history,
            updated_at
        ) VALUES (
            :id, :slug, :assistant_id, :name, :tagline, :category, :domain, :is_dynamic, :logo_url, :website_url,
            :primary_color, :secondary_color, :accent_color, :assistant_name,
            :welcome_message, :personality_prompt, :knowledge_base,
            :supported_languages, :contact_phone, :contact_email, :contact_address,
            :webhook_url, :allowed_domains, :is_active,
            :default_detail_level, :starter_prompts, :tone_of_voice, :enabled_components,
            :store_chat_history,
            CURRENT_TIMESTAMP
        )
        ON CONFLICT(id) DO UPDATE SET
            slug=excluded.slug,
            assistant_id=excluded.assistant_id,
            name=excluded.name,
            tagline=excluded.tagline,
            category=excluded.category,
            domain=excluded.domain,
            is_dynamic=excluded.is_dynamic,
            logo_url=excluded.logo_url,
            website_url=excluded.website_url,
            primary_color=excluded.primary_color,
            secondary_color=excluded.secondary_color,
            accent_color=excluded.accent_color,
            assistant_name=excluded.assistant_name,
            welcome_message=excluded.welcome_message,
            personality_prompt=excluded.personality_prompt,
            knowledge_base=excluded.knowledge_base,
            supported_languages=excluded.supported_languages,
            contact_phone=excluded.contact_phone,
            contact_email=excluded.contact_email,
            contact_address=excluded.contact_address,
            webhook_url=excluded.webhook_url,
            allowed_domains=excluded.allowed_domains,
            is_active=excluded.is_active,
            default_detail_level=excluded.default_detail_level,
            starter_prompts=excluded.starter_prompts,
            tone_of_voice=excluded.tone_of_voice,
            enabled_components=excluded.enabled_components,
            store_chat_history=excluded.store_chat_history,
            updated_at=CURRENT_TIMESTAMP;
        """, t)
        conn.commit()
        return t["id"]

def get_tenant_by_domain(domain: str) -> Optional[Dict[str, Any]]:
    """Finds a tenant by domain, website URL, or slug matching the hostname."""
    if not domain:
        return None
    clean = domain.lower().strip()
    if clean.startswith("https://") or clean.startswith("http://"):
        try:
            from urllib.parse import urlparse
            clean = urlparse(clean).hostname or clean
        except Exception:
            pass
    if clean.startswith("www."):
        clean = clean[4:]
    clean = clean.split(":")[0].strip()

    slug_candidate = clean.replace(".", "-")
    tenant_id_candidate = f"tenant_{clean.replace('.', '_')}"
    asst_id_candidate = f"asst_{clean.replace('.', '_')}"

    with get_connection() as conn:
        row = conn.execute("""
            SELECT * FROM tenants 
            WHERE LOWER(website_url) LIKE ? 
               OR LOWER(slug) = ? 
               OR LOWER(id) = ? 
               OR LOWER(assistant_id) = ?
               OR (domain != '' AND LOWER(domain) = ?)
            LIMIT 1;
        """, (f"%{clean}%", slug_candidate, tenant_id_candidate, asst_id_candidate, clean)).fetchone()
        return dict(row) if row else None

def delete_tenant(tenant_id: str) -> bool:
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM tenants WHERE id = ?;", (tenant_id,))
        conn.commit()
        return cursor.rowcount > 0

# --- Package CRUD Helpers ---

def get_tenant_packages(tenant_id: str) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM packages WHERE tenant_id = ? ORDER BY starting_price_inr ASC;", (tenant_id,)).fetchall()
        return [dict(r) for r in rows]

def set_tenant_packages(tenant_id: str, packages: List[Dict[str, Any]]):
    with get_connection() as conn:
        conn.execute("DELETE FROM packages WHERE tenant_id = ?;", (tenant_id,))
        for p in packages:
            conn.execute("""
            INSERT INTO packages (id, tenant_id, name, destination, duration, starting_price_inr, highlights, category, is_featured)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                p.get("id", f"pkg_{int(time.time()*1000)}_{p.get('destination', 'dest')}"),
                tenant_id,
                p["name"],
                p["destination"],
                p["duration"],
                int(p["starting_price_inr"]),
                p.get("highlights", ""),
                p.get("category", "Group Tour"),
                1 if p.get("is_featured", True) else 0
            ))
        conn.commit()

# --- Conversation & Message Helpers ---

def get_or_create_conversation(tenant_id: str, session_id: str) -> str:
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM conversations WHERE tenant_id = ? AND session_id = ?;", (tenant_id, session_id)).fetchone()
        if row:
            return row["id"]
        
        conv_id = f"conv_{int(time.time()*1000)}_{session_id[:8]}"
        conn.execute("INSERT INTO conversations (id, tenant_id, session_id) VALUES (?, ?, ?);", (conv_id, tenant_id, session_id))
        conn.commit()
        return conv_id

def save_turn(tenant_id: str, session_id: str, user_text: str, model_text: str):
    conv_id = get_or_create_conversation(tenant_id, session_id)
    with get_connection() as conn:
        conn.execute("INSERT INTO messages (conversation_id, tenant_id, role, text) VALUES (?, ?, 'user', ?);", (conv_id, tenant_id, user_text))
        conn.execute("INSERT INTO messages (conversation_id, tenant_id, role, text) VALUES (?, ?, 'model', ?);", (conv_id, tenant_id, model_text))
        conn.execute("UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?;", (conv_id,))
        conn.commit()

def get_conversation_history(tenant_id: str, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT m.role, m.text 
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE c.tenant_id = ? AND c.session_id = ?
            ORDER BY m.id DESC LIMIT ?;
        """, (tenant_id, session_id, limit)).fetchall()
        # Return chronological
        return [{"role": r["role"], "text": r["text"]} for r in reversed(rows)]

def list_tenant_conversations(tenant_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves stored chat sessions with timestamp, message count, and last message snippet."""
    with get_connection() as conn:
        query = """
            SELECT c.id, c.tenant_id, c.session_id, c.created_at, c.updated_at,
                   t.name AS tenant_name,
                   (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) AS message_count,
                   (SELECT m.text FROM messages m WHERE m.conversation_id = c.id ORDER BY m.id DESC LIMIT 1) AS last_message
            FROM conversations c
            JOIN tenants t ON c.tenant_id = t.id
        """
        params = []
        if tenant_id:
            query += " WHERE c.tenant_id = ?"
            params.append(tenant_id)
        query += " ORDER BY c.updated_at DESC LIMIT ?;"
        params.append(limit)
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

def get_conversation_messages(conversation_id: str) -> List[Dict[str, Any]]:
    """Retrieves full transcript messages for a given stored conversation."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, role, text, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC;
        """, (conversation_id,)).fetchall()
        return [dict(r) for r in rows]

# --- Lead Management Helpers ---

def insert_lead(lead: Dict[str, Any]) -> str:
    lead_id = lead.get("id", f"lead_{int(time.time()*1000)}")
    with get_connection() as conn:
        conn.execute("""
        INSERT INTO leads (
            id, tenant_id, session_id, customer_name, phone_number,
            destination, travel_type, pax_count, budget, travel_month,
            includes_seniors, lead_score, summary_notes, synced_to_webhook
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            lead_id,
            lead["tenant_id"],
            lead.get("session_id", ""),
            lead.get("customer_name", "Website Visitor"),
            lead["phone_number"],
            lead.get("destination", "General Inquiry"),
            lead.get("travel_type", "Not Specified"),
            lead.get("pax_count", "TBD"),
            lead.get("budget", "Standard"),
            lead.get("travel_month", "Flexible"),
            lead.get("includes_seniors", "No"),
            lead.get("lead_score", "HOT 🔥"),
            lead.get("summary_notes", ""),
            1 if lead.get("synced_to_webhook") else 0
        ))
        conn.commit()
    return lead_id

def list_tenant_leads(tenant_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        if tenant_id:
            rows = conn.execute("""
                SELECT l.*, t.name as tenant_name, t.slug as tenant_slug 
                FROM leads l
                JOIN tenants t ON l.tenant_id = t.id
                WHERE l.tenant_id = ? 
                ORDER BY l.created_at DESC LIMIT ?;
            """, (tenant_id, limit)).fetchall()
        else:
            rows = conn.execute("""
                SELECT l.*, t.name as tenant_name, t.slug as tenant_slug 
                FROM leads l
                JOIN tenants t ON l.tenant_id = t.id
                ORDER BY l.created_at DESC LIMIT ?;
            """, (limit,)).fetchall()
        return [dict(r) for r in rows]

def count_tenant_leads(tenant_id: Optional[str] = None) -> int:
    with get_connection() as conn:
        if tenant_id:
            row = conn.execute("SELECT COUNT(id) FROM leads WHERE tenant_id = ?;", (tenant_id,)).fetchone()
        else:
            row = conn.execute("SELECT COUNT(id) FROM leads;").fetchone()
        return row[0] if row else 0

def get_platform_analytics() -> Dict[str, Any]:
    with get_connection() as conn:
        total_tenants = conn.execute("SELECT COUNT(*) FROM tenants WHERE is_active = 1;").fetchone()[0]
        total_leads = conn.execute("SELECT COUNT(*) FROM leads;").fetchone()[0]
        total_conversations = conn.execute("SELECT COUNT(*) FROM conversations;").fetchone()[0]
        hot_leads = conn.execute("SELECT COUNT(*) FROM leads WHERE lead_score LIKE '%HOT%';").fetchone()[0]
        
        top_destinations = conn.execute("""
            SELECT destination, COUNT(*) as count 
            FROM leads 
            WHERE destination != 'General Inquiry' 
            GROUP BY destination 
            ORDER BY count DESC LIMIT 5;
        """).fetchall()

        return {
            "total_tenants": total_tenants,
            "total_leads": total_leads,
            "total_conversations": total_conversations,
            "hot_leads": hot_leads,
            "conversion_rate": f"{(hot_leads / max(total_conversations, 1) * 100):.1f}%",
            "top_destinations": [{"name": r["destination"], "count": r["count"]} for r in top_destinations]
        }

def verify_tenant_installation(tenant_id: str, verified: bool):
    """Updates physical installation verification status."""
    with get_connection() as conn:
        now_str = time.strftime("%Y-%m-%d %H:%M:%S") if verified else ""
        conn.execute("""
            UPDATE tenants 
            SET installation_verified = ?, installation_verified_at = ? 
            WHERE id = ?;
        """, (1 if verified else 0, now_str, tenant_id))
        conn.commit()

def update_tenant_settings(tenant_id: str, updates: Dict[str, Any]) -> bool:
    """Updates arbitrary tenant configuration fields safely."""
    allowed_keys = {
        "name", "tagline", "website_url", "primary_color", "secondary_color",
        "accent_color", "assistant_name", "welcome_message", "personality_prompt",
        "knowledge_base", "supported_languages", "contact_phone", "contact_email",
        "contact_address", "webhook_url", "allowed_domains", "feature_permissions",
        "usage_limits", "subscription_status", "is_active",
        "default_detail_level", "starter_prompts", "tone_of_voice", "enabled_components",
        "store_chat_history", "logo_url", "category", "domain"
    }
    filtered = {k: v for k, v in updates.items() if k in allowed_keys}
    if not filtered:
        return False
    
    set_clause = ", ".join([f"{k} = ?" for k in filtered.keys()])
    values = list(filtered.values()) + [tenant_id]

    with get_connection() as conn:
        conn.execute(f"UPDATE tenants SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?;", values)
        conn.commit()
        return True

def delete_lead(lead_id: str, tenant_id: Optional[str] = None) -> bool:
    """Deletes a lead record with optional tenant isolation check."""
    with get_connection() as conn:
        if tenant_id:
            cursor = conn.execute("DELETE FROM leads WHERE id = ? AND tenant_id = ?;", (lead_id, tenant_id))
        else:
            cursor = conn.execute("DELETE FROM leads WHERE id = ?;", (lead_id,))
        conn.commit()
        return cursor.rowcount > 0

def delete_conversation_data(tenant_id: str, session_id: str) -> bool:
    """GDPR/Privacy right-to-be-forgotten: deletes conversation, session context and associated messages."""
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM conversations WHERE tenant_id = ? AND session_id = ?;", (tenant_id, session_id))
        conn.execute("DELETE FROM session_contexts WHERE tenant_id = ? AND session_id = ?;", (tenant_id, session_id))
        conn.commit()
        return cursor.rowcount > 0

def save_feedback(tenant_id: str, session_id: str, rating: str, comment: str = ""):
    """Records user thumbs-up/thumbs-down feedback on assistant responses."""
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO feedback (tenant_id, session_id, rating, comment)
            VALUES (?, ?, ?, ?);
        """, (tenant_id, session_id, rating, comment))
        conn.commit()

# --- Structured Session Context & Memory Helpers ---

def get_session_context(tenant_id: str, session_id: str) -> Dict[str, Any]:
    """Retrieves structured cross-turn context memory for the session."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM session_contexts WHERE tenant_id = ? AND session_id = ?;", (tenant_id, session_id)).fetchone()
        if not row:
            return {
                "tenant_id": tenant_id,
                "session_id": session_id,
                "user_objective": "",
                "destination_interest": "",
                "budget_preference": "",
                "pax_count": "",
                "travel_month": "",
                "travel_type": "",
                "includes_seniors": False,
                "options_discussed": [],
                "collected_details": {},
                "unanswered_questions": [],
                "detail_mode": "standard",
                "last_user_message": "",
                "last_model_message": ""
            }
        
        d = dict(row)
        try:
            d["options_discussed"] = json.loads(d.get("options_discussed") or "[]")
        except Exception:
            d["options_discussed"] = []
        try:
            d["collected_details"] = json.loads(d.get("collected_details") or "{}")
        except Exception:
            d["collected_details"] = {}
        try:
            d["unanswered_questions"] = json.loads(d.get("unanswered_questions") or "[]")
        except Exception:
            d["unanswered_questions"] = []
        d["includes_seniors"] = bool(d.get("includes_seniors", 0))
        return d

def upsert_session_context(tenant_id: str, session_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Updates or creates structured cross-turn context memory for a session."""
    current = get_session_context(tenant_id, session_id)
    
    # Merge updates
    for k, v in updates.items():
        if k in current:
            current[k] = v

    ctx_id = f"ctx_{tenant_id}_{session_id}"
    options_json = json.dumps(current.get("options_discussed", []))
    collected_json = json.dumps(current.get("collected_details", {}))
    unanswered_json = json.dumps(current.get("unanswered_questions", []))

    with get_connection() as conn:
        conn.execute("""
        INSERT INTO session_contexts (
            id, tenant_id, session_id, user_objective, destination_interest,
            budget_preference, pax_count, travel_month, travel_type,
            includes_seniors, options_discussed, collected_details,
            unanswered_questions, detail_mode, last_user_message,
            last_model_message, updated_at
        ) VALUES (
            :id, :tenant_id, :session_id, :user_objective, :destination_interest,
            :budget_preference, :pax_count, :travel_month, :travel_type,
            :includes_seniors, :options_discussed, :collected_details,
            :unanswered_questions, :detail_mode, :last_user_message,
            :last_model_message, CURRENT_TIMESTAMP
        )
        ON CONFLICT(tenant_id, session_id) DO UPDATE SET
            user_objective=excluded.user_objective,
            destination_interest=excluded.destination_interest,
            budget_preference=excluded.budget_preference,
            pax_count=excluded.pax_count,
            travel_month=excluded.travel_month,
            travel_type=excluded.travel_type,
            includes_seniors=excluded.includes_seniors,
            options_discussed=excluded.options_discussed,
            collected_details=excluded.collected_details,
            unanswered_questions=excluded.unanswered_questions,
            detail_mode=excluded.detail_mode,
            last_user_message=excluded.last_user_message,
            last_model_message=excluded.last_model_message,
            updated_at=CURRENT_TIMESTAMP;
        """, {
            "id": ctx_id,
            "tenant_id": tenant_id,
            "session_id": session_id,
            "user_objective": current.get("user_objective", ""),
            "destination_interest": current.get("destination_interest", ""),
            "budget_preference": current.get("budget_preference", ""),
            "pax_count": current.get("pax_count", ""),
            "travel_month": current.get("travel_month", ""),
            "travel_type": current.get("travel_type", ""),
            "includes_seniors": 1 if current.get("includes_seniors") else 0,
            "options_discussed": options_json,
            "collected_details": collected_json,
            "unanswered_questions": unanswered_json,
            "detail_mode": current.get("detail_mode", "standard"),
            "last_user_message": current.get("last_user_message", ""),
            "last_model_message": current.get("last_model_message", "")
        })
        conn.commit()
    return current

def clear_session_context(tenant_id: str, session_id: str) -> bool:
    """Resets memory state for a fresh conversation."""
    with get_connection() as conn:
        conn.execute("DELETE FROM session_contexts WHERE tenant_id = ? AND session_id = ?;", (tenant_id, session_id))
        conn.commit()
        return True

def log_unanswered_question(tenant_id: str, session_id: str, question: str, reason: str = ""):
    """Logs when user asks a question that could not be satisfied from the knowledge base."""
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO unanswered_questions (tenant_id, session_id, question, reason)
            VALUES (?, ?, ?, ?);
        """, (tenant_id, session_id, question, reason or "Information not found in tenant knowledge base"))
        conn.commit()

def list_unanswered_questions(tenant_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Administrative report of recurring unanswered questions."""
    with get_connection() as conn:
        if tenant_id:
            rows = conn.execute("""
                SELECT u.*, t.name as tenant_name 
                FROM unanswered_questions u
                JOIN tenants t ON u.tenant_id = t.id
                WHERE u.tenant_id = ? 
                ORDER BY u.created_at DESC LIMIT ?;
            """, (tenant_id, limit)).fetchall()
        else:
            rows = conn.execute("""
                SELECT u.*, t.name as tenant_name 
                FROM unanswered_questions u
                JOIN tenants t ON u.tenant_id = t.id
                ORDER BY u.created_at DESC LIMIT ?;
            """, (limit,)).fetchall()
        return [dict(r) for r in rows]

def list_feedback(tenant_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Administrative report of customer feedback."""
    with get_connection() as conn:
        if tenant_id:
            rows = conn.execute("""
                SELECT f.*, t.name as tenant_name 
                FROM feedback f
                JOIN tenants t ON f.tenant_id = t.id
                WHERE f.tenant_id = ? 
                ORDER BY f.created_at DESC LIMIT ?;
            """, (tenant_id, limit)).fetchall()
        else:
            rows = conn.execute("""
                SELECT f.*, t.name as tenant_name 
                FROM feedback f
                JOIN tenants t ON f.tenant_id = t.id
                ORDER BY f.created_at DESC LIMIT ?;
            """, (limit,)).fetchall()
        return [dict(r) for r in rows]

