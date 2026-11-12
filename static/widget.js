/**
 * Devlancer Universal Embeddable AI Chatbot Widget
 * Version: 4.0.0 – Advanced Interactive & Rich Component Edition
 * 
 * Multi-tenant AI digital travel consultant featuring:
 * - Shadow DOM CSS isolation
 * - Component-Based Response System (Cards, Comparison Tables, Itineraries, Steps, Accordions, Checklists, Budget)
 * - Response Detail Level Switcher (Quick | Standard | Detailed)
 * - Smart Follow-Up Questions with Interactive Chips
 * - Validated Conversation Action Engine
 * - Explicit User Consent for Enquiry Confirmation
 * - Cross-Turn Conversation Memory with Reset Controls
 * - Voice Input (Speech-to-Text) & Voice Output (Text-to-Speech)
 * - Factual Grounding & Source Citations
 * - Interactive Trip Budget Calculator & Packages Browser
 */

(function () {
  'use strict';

  // 1. Script tag resolution
  const currentScript = document.currentScript || (function () {
    const scripts = document.getElementsByTagName('script');
    for (let i = scripts.length - 1; i >= 0; i--) {
      if (scripts[i].src && scripts[i].src.indexOf('widget.js') !== -1) {
        return scripts[i];
      }
    }
    return null;
  })();

  const assistantId = currentScript ? (currentScript.getAttribute('data-assistant-id') || currentScript.getAttribute('data-tenant-id')) : null;
  const scriptTenantSlug = currentScript ? (currentScript.getAttribute('data-tenant-slug') || currentScript.getAttribute('data-slug')) : null;
  const scriptDomain = currentScript ? currentScript.getAttribute('data-domain') : null;
  const scriptLogoUrl = currentScript ? currentScript.getAttribute('data-logo-url') : null;
  
  let baseUrl = window.location.origin;
  if (currentScript && currentScript.src) {
    try {
      const parsedUrl = new URL(currentScript.src);
      baseUrl = parsedUrl.origin;
    } catch (e) {}
  }

  if (window.__DEVLANCER_WIDGET_LOADED__) return;
  window.__DEVLANCER_WIDGET_LOADED__ = true;

  // Session state
  const SESSION_ID = "devlancer_sess_" + Math.random().toString(36).substring(2, 9);
  let tenantConfig = null;
  let isOpen = false;
  let isMaximized = false;
  let isRecording = false;
  let speechRec = null;
  let currentDetailMode = "standard"; // "quick", "standard", "detailed"
  let conversationHistory = [];

  // Helper: Sniff host context, theme, and metadata
  function sniffHostContext() {
    let host = scriptDomain || window.location.hostname || '';
    if (host === 'localhost' || host === '127.0.0.1' || !host) {
      try {
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('test_domain')) {
          host = urlParams.get('test_domain');
        } else if (urlParams.get('url')) {
          const parsed = new URL(urlParams.get('url').startsWith('http') ? urlParams.get('url') : `https://${urlParams.get('url')}`);
          host = parsed.hostname;
        }
      } catch (e) {}
    }
    const themeMeta = document.querySelector('meta[name="theme-color"]');
    const themeColor = themeMeta ? themeMeta.getAttribute('content') : '';
    const descMeta = document.querySelector('meta[name="description"]') || document.querySelector('meta[property="og:description"]');
    const metaDesc = descMeta ? descMeta.getAttribute('content') : '';
    const siteNameMeta = document.querySelector('meta[property="og:site_name"]');
    const siteName = siteNameMeta ? siteNameMeta.getAttribute('content') : '';
    const title = document.title || '';
    return { host, themeColor, metaDesc, siteName, title };
  }

  // 2. Fetch Public Configuration
  async function fetchConfig() {
    try {
      const sniff = sniffHostContext();
      let query = '';
      if (assistantId && assistantId !== 'auto' && assistantId !== 'default') {
        query = `assistant_id=${encodeURIComponent(assistantId)}`;
      } else if (scriptTenantSlug && scriptTenantSlug !== 'auto' && scriptTenantSlug !== 'default') {
        query = `tenant_slug=${encodeURIComponent(scriptTenantSlug)}`;
      } else if (sniff.host && sniff.host !== 'localhost' && sniff.host !== '127.0.0.1') {
        query = `domain=${encodeURIComponent(sniff.host)}&title=${encodeURIComponent(sniff.title)}&meta_desc=${encodeURIComponent(sniff.metaDesc || '')}&theme_color=${encodeURIComponent(sniff.themeColor || '')}`;
      } else {
        query = `assistant_id=asst_prakruthi_kammanahalli`;
      }
      const url = `${baseUrl}/api/widget/config?${query}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error("Failed to load widget config");
      tenantConfig = await res.json();
      currentDetailMode = tenantConfig.default_detail_level || "standard";
      initWidget();
    } catch (err) {
      console.warn("[Devlancer AI Widget] Error loading config, using fallback:", err);
      tenantConfig = {
        name: "Devlancer Travel AI",
        assistant_name: "Travel Concierge",
        slug: "prakruthi-holidays",
        primary_color: "#18181b",
        secondary_color: "#09090b",
        accent_color: "#3b82f6",
        welcome_message: "Hello! Welcome to our travel concierge. How can we assist your trip planning today?",
        contact_phone: "+91 9845370515",
        default_detail_level: "standard",
        starter_prompts: ["Explore Top Packages", "Plan a 5-Day Trip", "Senior Citizen Tours", "Cancellation Policies"],
        packages: []
      };
      initWidget();
    }
  }

  // Helper: Escape HTML
  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // 3. Mount Isolated Shadow DOM Widget
  function initWidget() {
    const container = document.createElement('div');
    container.id = 'devlancer-ai-widget-root';
    document.body.appendChild(container);

    const shadow = container.attachShadow({ mode: 'open' });

    // Styles inside Shadow DOM
    const style = document.createElement('style');
    style.textContent = `
      * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, sans-serif; }
      
      #launcher-btn {
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 2147483640;
        background: #09090b;
        color: #fafafa;
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 9999px;
        padding: 10px 18px;
        font-size: 13px;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 8px;
        cursor: pointer;
        box-shadow: 0 12px 32px -4px rgba(0, 0, 0, 0.35);
        transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), background 0.15s, border-color 0.15s;
        letter-spacing: -0.01em;
      }
      #launcher-btn:hover { transform: translateY(-2px); background: #18181b; border-color: rgba(255, 255, 255, 0.25); }
      #launcher-btn:active { transform: translateY(0); }

      .launcher-avatar {
        width: 19px;
        height: 19px;
        border-radius: 5px;
        overflow: hidden;
        background: #ffffff;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.2);
        margin-right: 1px;
      }
      .launcher-avatar img {
        width: 100%;
        height: 100%;
        object-fit: contain;
        display: block;
      }
      .launcher-avatar-fallback {
        width: 100%;
        height: 100%;
        background: #18181b;
        color: #ffffff;
        font-size: 8.5px;
        font-weight: 700;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .launcher-dot {
        width: 6.5px;
        height: 6.5px;
        border-radius: 50%;
        background: #10b981;
      }

      #chat-window {
        position: fixed;
        bottom: 84px;
        right: 24px;
        width: 420px;
        height: 640px;
        max-width: calc(100vw - 32px);
        max-height: calc(100vh - 100px);
        background: #ffffff;
        border-radius: 16px;
        box-shadow: 0 20px 40px -15px rgba(0,0,0,0.2), 0 0 0 1px rgba(0,0,0,0.06);
        z-index: 2147483645;
        display: none;
        flex-direction: column;
        overflow: hidden;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
      }

      #chat-window.maximized {
        bottom: 16px;
        right: 16px;
        left: 16px;
        top: 16px;
        width: auto;
        height: auto;
        max-width: none;
        max-height: none;
        border-radius: 16px;
      }

      /* Header */
      .header {
        background: #09090b;
        color: #ffffff;
        padding: 12px 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 1px solid rgba(255,255,255,0.08);
        flex-shrink: 0;
        position: relative;
      }

      .header-title-box { display: flex; align-items: center; gap: 10px; min-width: 0; }
      .header-avatar {
        width: 32px;
        height: 32px;
        border-radius: 8px;
        background: #ffffff;
        color: #18181b;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
        font-weight: 700;
        border: 1px solid rgba(255,255,255,0.15);
        flex-shrink: 0;
        overflow: hidden;
        position: relative;
        box-shadow: 0 2px 6px rgba(0,0,0,0.25);
      }
      .header-avatar img {
        width: 100%;
        height: 100%;
        object-fit: contain;
        display: block;
        padding: 2px;
        background: #ffffff;
      }
      .header-avatar-initial {
        width: 100%;
        height: 100%;
        background: #18181b;
        color: #ffffff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
        font-weight: 700;
      }
      .header-name { font-size: 13px; font-weight: 600; color: #f4f4f5; line-height: 1.2; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      .header-sub { font-size: 10.5px; color: #a1a1aa; display: flex; align-items: center; gap: 4px; margin-top: 1.5px; }
      .status-dot { width: 5.5px; height: 5.5px; border-radius: 50%; background: #10b981; display: inline-block; }

      .bot-msg-meta {
        display: flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 7px;
      }
      .bot-msg-avatar {
        width: 19px;
        height: 19px;
        border-radius: 5px;
        overflow: hidden;
        background: #ffffff;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid rgba(0,0,0,0.08);
        box-shadow: 0 1px 2px rgba(0,0,0,0.06);
        flex-shrink: 0;
      }
      .bot-msg-avatar img {
        width: 100%;
        height: 100%;
        object-fit: contain;
        display: block;
        padding: 1.5px;
      }
      .bot-msg-avatar .avatar-initial {
        width: 100%;
        height: 100%;
        background: #27272a;
        color: #e4e4e7;
        font-size: 8px;
        font-weight: 700;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      .bot-msg-sender {
        font-size: 11px;
        font-weight: 600;
        color: #71717a;
        letter-spacing: -0.01em;
      }

      .header-actions { display: flex; align-items: center; gap: 4px; }
      .btn-icon {
        width: 28px;
        height: 28px;
        border-radius: 6px;
        background: transparent;
        border: 1px solid transparent;
        color: #a1a1aa;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: background 0.15s, color 0.15s;
      }
      .btn-icon:hover { background: rgba(255,255,255,0.08); color: #ffffff; }

      /* Dropdown Menu */
      .header-menu {
        position: absolute;
        top: 50px;
        right: 14px;
        background: #111113;
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 10px;
        box-shadow: 0 16px 36px rgba(0,0,0,0.4);
        width: 210px;
        display: none;
        flex-direction: column;
        z-index: 50;
        overflow: hidden;
      }
      .header-menu.active { display: flex; }
      .menu-item {
        padding: 9px 12px;
        font-size: 11.5px;
        color: #d4d4d8;
        display: flex;
        align-items: center;
        gap: 8px;
        cursor: pointer;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        text-decoration: none;
        background: transparent;
        transition: background 0.1s;
      }
      .menu-item:last-child { border-bottom: none; }
      .menu-item:hover { background: #18181b; color: #ffffff; }

      /* Detail Mode Segmented Control */
      .mode-bar {
        background: #f8fafc;
        border-bottom: 1px solid #e2e8f0;
        padding: 6px 14px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 11px;
        flex-shrink: 0;
      }
      .mode-label { color: #64748b; font-weight: 500; font-size: 10.5px; }
      .mode-switcher {
        display: inline-flex;
        background: #e2e8f0;
        border-radius: 6px;
        padding: 2px;
        gap: 2px;
      }
      .mode-btn {
        border: none;
        background: transparent;
        color: #64748b;
        font-size: 10px;
        font-weight: 600;
        padding: 2px 7px;
        border-radius: 4px;
        cursor: pointer;
        transition: all 0.15s;
      }
      .mode-btn.active {
        background: #ffffff;
        color: #09090b;
        box-shadow: 0 1px 2px rgba(0,0,0,0.06);
      }

      /* Quick Actions Toolbar */
      .quick-actions-bar {
        display: flex;
        gap: 6px;
        padding: 7px 14px;
        background: #ffffff;
        border-bottom: 1px solid #f1f5f9;
        flex-shrink: 0;
      }
      .action-pill-btn {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        color: #475569;
        border-radius: 7px;
        padding: 4px 9px;
        font-size: 11px;
        font-weight: 500;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 4px;
        transition: background 0.15s;
      }
      .action-pill-btn:hover { background: #f1f5f9; color: #09090b; }

      /* Messages Feed */
      .messages-container {
        flex: 1;
        overflow-y: auto;
        padding: 14px;
        display: flex;
        flex-direction: column;
        gap: 12px;
        background: #fcfcfd;
        position: relative;
      }
      .message-wrapper { display: flex; flex-direction: column; max-width: 90%; }
      .bot-wrapper { align-self: flex-start; }
      .user-wrapper { align-self: flex-end; }

      .user-bubble {
        background: #09090b;
        color: #ffffff;
        padding: 9px 13px;
        border-radius: 14px 14px 2px 14px;
        font-size: 12.5px;
        line-height: 1.45;
        word-break: break-word;
      }

      .bot-bubble {
        background: #ffffff;
        color: #18181b;
        border: 1px solid #e4e4e7;
        padding: 11px 14px;
        border-radius: 14px 14px 14px 2px;
        font-size: 12.5px;
        line-height: 1.5;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02);
      }

      .typing-dots {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 2px 4px;
      }
      .typing-dot {
        width: 6px;
        height: 6px;
        background-color: ${primaryColor || '#047857'};
        border-radius: 50%;
        opacity: 0.7;
        animation: typingBounce 1.2s infinite ease-in-out both;
      }
      .typing-dot:nth-child(1) { animation-delay: -0.32s; }
      .typing-dot:nth-child(2) { animation-delay: -0.16s; }
      @keyframes typingBounce {
        0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
        40% { transform: scale(1.15); opacity: 1; }
      }

      /* ========================================================= */
      /* RICH RESPONSE COMPONENTS STYLING                          */
      /* ========================================================= */

      /* 1. Answer Summary */
      .ans-summary {
        background: #f4f4f5;
        border-left: 3px solid #18181b;
        padding: 7px 10px;
        border-radius: 0 6px 6px 0;
        font-size: 11.5px;
        font-weight: 500;
        color: #27272a;
        margin-bottom: 8px;
      }

      /* 2. Structured Cards Grid */
      .ans-cards-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 8px;
        margin: 10px 0;
      }
      .info-card {
        background: #fafafa;
        border: 1px solid #e4e4e7;
        border-radius: 9px;
        padding: 10px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: border-color 0.15s;
      }
      .info-card:hover { border-color: #a1a1aa; }
      .card-badge {
        display: inline-block;
        font-size: 9px;
        font-weight: 600;
        text-transform: uppercase;
        padding: 2px 6px;
        border-radius: 4px;
        background: #e4e4e7;
        color: #27272a;
        width: fit-content;
        margin-bottom: 4px;
      }
      .card-title { font-size: 12px; font-weight: 600; color: #09090b; line-height: 1.25; }
      .card-duration { font-size: 10.5px; color: #71717a; margin-top: 2px; }
      .card-price { font-size: 12px; font-weight: 700; color: #09090b; margin: 4px 0; }
      .card-highlights { list-style: none; margin: 5px 0 8px 0; padding: 0; }
      .card-highlights li {
        font-size: 10.5px;
        color: #52525b;
        position: relative;
        padding-left: 12px;
        margin-bottom: 2px;
      }
      .card-highlights li::before {
        content: "•";
        position: absolute;
        left: 2px;
        color: #71717a;
      }
      .card-actions { display: flex; gap: 4px; margin-top: 6px; }

      /* 3. Comparison Table */
      .comp-table-wrap {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        border: 1px solid #e4e4e7;
        border-radius: 8px;
        margin: 10px 0;
        background: #ffffff;
      }
      .comp-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 11px;
        text-align: left;
      }
      .comp-table th {
        background: #f4f4f5;
        color: #18181b;
        padding: 6px 9px;
        font-weight: 600;
        border-bottom: 1px solid #e4e4e7;
        white-space: nowrap;
      }
      .comp-table td {
        padding: 6px 9px;
        border-bottom: 1px solid #f4f4f5;
        color: #3f3f46;
      }
      .comp-table tr:nth-child(even) td { background: #fafafa; }
      .comp-highlights-footer {
        padding: 6px 9px;
        background: #f8fafc;
        font-size: 10.5px;
        color: #475569;
        border-top: 1px solid #e2e8f0;
      }

      /* 4. Day-by-Day Itinerary */
      .itinerary-timeline {
        border-left: 2px solid #e4e4e7;
        margin: 10px 0 10px 8px;
        padding-left: 14px;
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      .itinerary-day { position: relative; }
      .day-marker {
        position: absolute;
        left: -20px;
        top: 2px;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #18181b;
        border: 2px solid #ffffff;
      }
      .day-heading { font-size: 12px; font-weight: 600; color: #09090b; }
      .day-block { font-size: 11px; color: #3f3f46; margin-top: 3px; line-height: 1.4; }
      .day-block strong { color: #18181b; font-size: 10.5px; }
      .day-tag {
        display: inline-block;
        font-size: 9.5px;
        padding: 1px 6px;
        border-radius: 4px;
        background: #f4f4f5;
        color: #52525b;
        margin-top: 3px;
      }

      /* 5. Steps Instructions */
      .steps-box { display: flex; flex-direction: column; gap: 6px; margin: 8px 0; }
      .step-row {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        background: #fafafa;
        border: 1px solid #e4e4e7;
        border-radius: 7px;
        padding: 7px 9px;
      }
      .step-badge {
        width: 18px;
        height: 18px;
        border-radius: 50%;
        background: #18181b;
        color: #ffffff;
        font-size: 10px;
        font-weight: 600;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
      }
      .step-text { font-size: 11px; color: #27272a; }
      .step-text strong { display: block; color: #09090b; font-size: 11.5px; margin-bottom: 1px; }

      /* 6. Expandable Accordions */
      .accordion-group { margin: 8px 0; display: flex; flex-direction: column; gap: 5px; }
      .ans-accordion {
        border: 1px solid #e4e4e7;
        border-radius: 7px;
        background: #fafafa;
        overflow: hidden;
      }
      .ans-accordion summary {
        padding: 7px 10px;
        font-size: 11px;
        font-weight: 600;
        color: #18181b;
        cursor: pointer;
        user-select: none;
        list-style: none;
        display: flex;
        align-items: center;
        justify-content: space-between;
      }
      .ans-accordion summary::-webkit-details-marker { display: none; }
      .ans-accordion-body {
        padding: 8px 10px;
        font-size: 11px;
        color: #52525b;
        border-top: 1px solid #f4f4f5;
        background: #ffffff;
        line-height: 1.45;
      }

      /* 7. Interactive Checklists */
      .checklist-card {
        background: #fafafa;
        border: 1px solid #e4e4e7;
        border-radius: 8px;
        padding: 8px 10px;
        margin: 8px 0;
      }
      .checklist-title { font-size: 11px; font-weight: 600; color: #18181b; margin-bottom: 6px; }
      .check-item {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 11px;
        color: #3f3f46;
        margin: 3px 0;
        cursor: pointer;
      }
      .check-item input[type="checkbox"] { cursor: pointer; accent-color: #18181b; }

      /* 8. Budget Breakdown */
      .budget-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 9px;
        margin: 8px 0;
      }
      .budget-row {
        display: flex;
        justify-content: space-between;
        font-size: 11px;
        color: #475569;
        padding: 3px 0;
        border-bottom: 1px solid #f1f5f9;
      }
      .budget-row:last-child { border-bottom: none; }
      .budget-total-row {
        display: flex;
        justify-content: space-between;
        font-size: 12px;
        font-weight: 700;
        color: #0f172a;
        margin-top: 6px;
        padding-top: 6px;
        border-top: 1px solid #cbd5e1;
      }

      /* 9. Verified Source Citations */
      .sources-box { margin-top: 6px; display: flex; flex-wrap: wrap; gap: 4px; }
      .source-chip {
        font-size: 9.5px;
        background: #f4f4f5;
        color: #71717a;
        border: 1px solid #e4e4e7;
        border-radius: 4px;
        padding: 2px 6px;
        display: inline-flex;
        align-items: center;
        gap: 3px;
      }

      /* 10. Smart Follow-Up with Chips */
      .followup-box {
        background: #faf5ff;
        border: 1px solid #e9d5ff;
        border-radius: 9px;
        padding: 9px;
        margin-top: 9px;
      }
      .followup-q { font-size: 11.5px; font-weight: 600; color: #581c87; margin-bottom: 6px; }
      .followup-chips { display: flex; flex-wrap: wrap; gap: 4px; }
      .chip-btn {
        background: #ffffff;
        border: 1px solid #c084fc;
        color: #6b21a8;
        border-radius: 9999px;
        padding: 3px 9px;
        font-size: 10.5px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.15s;
      }
      .chip-btn:hover { background: #f3e8ff; border-color: #9333ea; }

      /* 11. Contextual Action Buttons */
      .actions-container {
        display: flex;
        flex-wrap: wrap;
        gap: 5px;
        margin-top: 8px;
      }
      .action-btn {
        background: #18181b;
        color: #ffffff;
        border: none;
        border-radius: 6px;
        padding: 5px 10px;
        font-size: 11px;
        font-weight: 500;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 4px;
        transition: background 0.15s;
      }
      .action-btn:hover { background: #09090b; }
      .action-btn.secondary {
        background: #ffffff;
        color: #27272a;
        border: 1px solid #e4e4e7;
      }
      .action-btn.secondary:hover { background: #f4f4f5; }

      /* 12. Explicit Confirmation Card */
      .confirm-enquiry-card {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 9px;
        padding: 10px;
        margin: 8px 0;
        font-size: 11.5px;
        color: #166534;
      }
      .confirm-enquiry-card h5 { font-size: 12px; font-weight: 700; color: #14532d; margin-bottom: 4px; }
      .confirm-details { font-family: monospace; font-size: 10.5px; background: rgba(255,255,255,0.7); padding: 6px; border-radius: 5px; margin: 6px 0; }
      .confirm-btns { display: flex; gap: 6px; margin-top: 6px; }

      /* Message Actions (Copy, TTS, Thumbs) */
      .msg-actions {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-top: 8px;
        padding-top: 6px;
        border-top: 1px solid #f4f4f5;
        font-size: 10px;
        color: #a1a1aa;
      }
      .action-btns { display: flex; align-items: center; gap: 8px; }
      .action-link {
        color: #71717a;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 3px;
        font-weight: 500;
        text-decoration: none;
        transition: color 0.15s;
      }
      .action-link:hover { color: #18181b; }
      .feedback-btn {
        cursor: pointer;
        opacity: 0.5;
        transition: opacity 0.15s;
        font-size: 11px;
      }
      .feedback-btn:hover { opacity: 1; }
      .feedback-btn.active { opacity: 1; color: #09090b; }

      /* Floating Scroll Down Pill */
      #scroll-down-btn {
        position: absolute;
        bottom: 12px;
        left: 50%;
        transform: translateX(-50%);
        background: #ffffff;
        color: #3f3f46;
        border: 1px solid #e4e4e7;
        border-radius: 9999px;
        padding: 4px 10px;
        font-size: 10.5px;
        font-weight: 500;
        cursor: pointer;
        display: none;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        z-index: 20;
      }

      /* Quick Replies */
      .quick-replies {
        display: flex;
        gap: 5px;
        overflow-x: auto;
        padding: 7px 14px;
        background: #ffffff;
        border-top: 1px solid #f4f4f5;
        flex-shrink: 0;
      }
      .quick-chip {
        white-space: nowrap;
        background: #f4f4f5;
        color: #3f3f46;
        border: 1px solid #e4e4e7;
        border-radius: 9999px;
        padding: 4px 10px;
        font-size: 10.5px;
        font-weight: 500;
        cursor: pointer;
        transition: background 0.15s, color 0.15s;
      }
      .quick-chip:hover { background: #e4e4e7; color: #18181b; }

      /* Input Composer */
      .composer {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 9px 14px;
        background: #ffffff;
        border-top: 1px solid #f1f5f9;
        flex-shrink: 0;
      }
      .chat-input {
        flex: 1;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 8px 11px;
        font-size: 12px;
        color: #0f172a;
        outline: none;
        transition: border 0.15s, background 0.15s;
      }
      .chat-input:focus { border-color: #71717a; background: #ffffff; }

      .send-btn {
        background: #09090b;
        color: #ffffff;
        border: none;
        border-radius: 9px;
        padding: 8px 12px;
        font-size: 11.5px;
        font-weight: 500;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 3px;
        transition: background 0.15s;
      }
      .send-btn:hover { background: #27272a; }
      .send-btn:disabled { opacity: 0.5; cursor: not-allowed; }

      .powered-by {
        text-align: center;
        font-size: 9.5px;
        color: #a1a1aa;
        padding: 4px;
        background: #ffffff;
        border-top: 1px solid #fafafa;
      }
      .powered-by a { color: #71717a; text-decoration: none; font-weight: 500; }
      .powered-by a:hover { color: #18181b; }

      /* Calculator Overlay */
      #calc-overlay {
        position: absolute;
        inset: 0;
        background: rgba(0,0,0,0.5);
        backdrop-filter: blur(2px);
        z-index: 60;
        display: none;
        align-items: center;
        justify-content: center;
        padding: 16px;
      }
      .calc-modal {
        background: #ffffff;
        border-radius: 14px;
        padding: 16px;
        width: 100%;
        max-width: 330px;
        box-shadow: 0 16px 36px rgba(0,0,0,0.25);
        font-size: 12px;
      }
      .calc-modal h4 { font-size: 13px; font-weight: 600; color: #18181b; margin-bottom: 8px; }
      .calc-input { width: 100%; padding: 6px 9px; border: 1px solid #e4e4e7; border-radius: 7px; margin-bottom: 8px; font-size: 11.5px; outline: none; }
      .calc-input:focus { border-color: #71717a; }
      .calc-res-box { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 9px; margin: 8px 0; text-align: center; }
      .calc-price { font-size: 17px; font-weight: 700; color: #09090b; }

      /* ========================================================= */
      /* DARK THEME STYLES                                         */
      /* ========================================================= */
      #chat-window.dark-theme {
        background: #0f0f12;
        box-shadow: 0 20px 40px -15px rgba(0,0,0,0.8), 0 0 0 1px rgba(255,255,255,0.1);
      }
      #chat-window.dark-theme .mode-bar {
        background: #141418;
        border-bottom: 1px solid rgba(255,255,255,0.08);
      }
      #chat-window.dark-theme .mode-label { color: #a1a1aa; }
      #chat-window.dark-theme .mode-switcher {
        background: #1e1e24;
        border-color: rgba(255,255,255,0.1);
      }
      #chat-window.dark-theme .mode-btn { color: #a1a1aa; }
      #chat-window.dark-theme .mode-btn.active {
        background: #2e2e38;
        color: #ffffff;
      }
      #chat-window.dark-theme .quick-actions-bar {
        background: #141418;
        border-bottom: 1px solid rgba(255,255,255,0.08);
      }
      #chat-window.dark-theme .action-pill-btn {
        background: #1e1e24;
        border-color: rgba(255,255,255,0.1);
        color: #e4e4e7;
      }
      #chat-window.dark-theme .action-pill-btn:hover {
        background: #272730;
        color: #ffffff;
      }
      #chat-window.dark-theme .messages-container {
        background: #09090b;
      }
      #chat-window.dark-theme .bot-bubble {
        background: #16161a;
        border: 1px solid rgba(255,255,255,0.08);
        color: #e4e4e7;
      }
      #chat-window.dark-theme .bot-bubble strong { color: #ffffff; }
      #chat-window.dark-theme .bot-bubble p, 
      #chat-window.dark-theme .bot-bubble li { color: #d4d4d8; }
      #chat-window.dark-theme .bot-bubble blockquote {
        background: #1c1c22;
        border-left-color: #60a5fa;
        color: #e4e4e7;
      }
      #chat-window.dark-theme .bot-msg-sender { color: #a1a1aa; }
      #chat-window.dark-theme .quick-replies {
        background: #141418;
        border-top: 1px solid rgba(255,255,255,0.08);
      }
      #chat-window.dark-theme .quick-chip {
        background: #1e1e24;
        border-color: rgba(255,255,255,0.1);
        color: #e4e4e7;
      }
      #chat-window.dark-theme .quick-chip:hover {
        background: #272730;
        color: #ffffff;
      }
      #chat-window.dark-theme .composer {
        background: #141418;
        border-top: 1px solid rgba(255,255,255,0.08);
      }
      #chat-window.dark-theme .chat-input {
        background: #1a1a20;
        border-color: rgba(255,255,255,0.12);
        color: #ffffff;
      }
      #chat-window.dark-theme .chat-input:focus {
        border-color: #a1a1aa;
        background: #202028;
      }
      #chat-window.dark-theme #mic-btn {
        background: #1e1e24 !important;
        border-color: rgba(255,255,255,0.1) !important;
        color: #a1a1aa !important;
      }
      #chat-window.dark-theme .powered-by {
        background: #141418;
        border-top: 1px solid rgba(255,255,255,0.05);
        color: #71717a;
      }
      #chat-window.dark-theme .powered-by a { color: #a1a1aa; }
      #chat-window.dark-theme .comp-table {
        background: #16161a;
        border-color: rgba(255,255,255,0.1);
      }
      #chat-window.dark-theme .comp-table th {
        background: #22222a;
        color: #f4f4f5;
        border-bottom-color: rgba(255,255,255,0.1);
      }
      #chat-window.dark-theme .comp-table td {
        background: #16161a;
        color: #d4d4d8;
        border-bottom-color: rgba(255,255,255,0.06);
      }
      #chat-window.dark-theme .card-item {
        background: #1a1a20;
        border-color: rgba(255,255,255,0.1);
        color: #f4f4f5;
      }
      #chat-window.dark-theme .card-item-title { color: #ffffff; }
      #chat-window.dark-theme .card-item-sub { color: #a1a1aa; }
      #chat-window.dark-theme .follow-up-box {
        background: #1c182a;
        border-color: rgba(168,85,247,0.3);
      }
      #chat-window.dark-theme .follow-up-chip {
        background: #27213d;
        border-color: rgba(168,85,247,0.4);
        color: #e9d5ff;
      }
      #chat-window.dark-theme .calc-modal {
        background: #16161a;
        color: #f4f4f5;
        border: 1px solid rgba(255,255,255,0.1);
      }
      #chat-window.dark-theme .calc-modal h4 { color: #ffffff; }
      #chat-window.dark-theme .calc-input {
        background: #1e1e24;
        border-color: rgba(255,255,255,0.15);
        color: #ffffff;
      }
      #chat-window.dark-theme .calc-res-box {
        background: #1e1e24;
        border-color: rgba(255,255,255,0.1);
      }
      #chat-window.dark-theme .calc-price { color: #ffffff; }
    `;
    shadow.appendChild(style);

    const initial = (tenantConfig.name || 'AI').slice(0, 2).toUpperCase();

    // Dynamically resolve website logo
    let logoUrl = (tenantConfig.logo_url || scriptLogoUrl || '').trim();
    if (!logoUrl && tenantConfig.website_url) {
      try {
        const u = new URL(tenantConfig.website_url.startsWith('http') ? tenantConfig.website_url : 'https://' + tenantConfig.website_url);
        const host = u.hostname.replace(/^www\./, '');
        logoUrl = `https://www.google.com/s2/favicons?domain=${encodeURIComponent(host)}&sz=128`;
      } catch (e) {}
    }
    if (!logoUrl) {
      const pageFavicon = document.querySelector('link[rel="apple-touch-icon"]')?.href ||
                          document.querySelector('link[rel~="icon"]')?.href;
      if (pageFavicon) logoUrl = pageFavicon;
    }

    // Launcher Button
    const launcher = document.createElement('button');
    launcher.id = 'launcher-btn';
    launcher.setAttribute('aria-label', `Open ${tenantConfig.assistant_name || 'Concierge'} Chat`);
    launcher.innerHTML = `
      ${logoUrl ? `
        <div class="launcher-avatar">
          <img src="${escapeHtml(logoUrl)}" alt="${escapeHtml(tenantConfig.name)}" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" />
          <div class="launcher-avatar-fallback" style="display:none;">${initial}</div>
        </div>
      ` : `<span class="launcher-dot"></span>`}
      <span>${escapeHtml(tenantConfig.assistant_name || 'Concierge')}</span>
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path></svg>
    `;
    launcher.onclick = toggleChat;
    shadow.appendChild(launcher);

    // Chat Window
    const win = document.createElement('div');
    win.id = 'chat-window';
    win.innerHTML = `
      <div class="header">
        <div class="header-title-box">
          <div class="header-avatar">
            ${logoUrl ? `
              <img src="${escapeHtml(logoUrl)}" alt="${escapeHtml(tenantConfig.name)}" class="header-logo-img" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" />
              <div class="header-avatar-initial" style="display:none;">${initial}</div>
            ` : `
              <div class="header-avatar-initial">${initial}</div>
            `}
          </div>
          <div style="min-width: 0;">
            <div class="header-name">${escapeHtml(tenantConfig.name || 'Travel Concierge')}</div>
            <div class="header-sub">
              <span class="status-dot"></span>
              <span>Online • ${escapeHtml(tenantConfig.supported_languages || 'English')}</span>
            </div>
          </div>
        </div>
        <div class="header-actions">
          <button class="btn-icon" id="theme-btn" title="Toggle Light / Dark Mode" aria-label="Toggle theme">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
          </button>
          <button class="btn-icon" id="max-btn" title="Expand / Restore" aria-label="Expand view">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"></path></svg>
          </button>
          <button class="btn-icon" id="menu-btn" title="Options" aria-label="Menu">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="1"></circle><circle cx="12" cy="5" r="1"></circle><circle cx="12" cy="19" r="1"></circle></svg>
          </button>
          <button class="btn-icon" id="close-btn" title="Close" aria-label="Close chat">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"></path></svg>
          </button>
        </div>

        <!-- Dropdown Menu -->
        <div class="header-menu" id="header-menu">
          <div class="menu-item" id="opt-theme-toggle">🌓 Toggle Light / Dark Theme</div>
          <div class="menu-item" id="opt-new-chat">New Conversation</div>
          <div class="menu-item" id="opt-regenerate">Regenerate Last Answer</div>
          <div class="menu-item" id="opt-copy-chat">Export Transcript</div>
          ${tenantConfig.contact_phone ? `<a href="tel:${tenantConfig.contact_phone}" class="menu-item">Call Desk (${escapeHtml(tenantConfig.contact_phone)})</a>` : ''}
          <div class="menu-item" id="opt-privacy">Clear & Privacy Rights</div>
          <a href="${baseUrl}/c/${tenantConfig.slug || 'prakruthi-holidays'}" target="_blank" class="menu-item">Open Portal ↗</a>
        </div>
      </div>

      <!-- Detail Mode Segmented Control Bar -->
      <div class="mode-bar">
        <span class="mode-label">Answer Detail</span>
        <div class="mode-switcher" id="mode-switcher">
          <button type="button" class="mode-btn ${currentDetailMode === 'quick' ? 'active' : ''}" data-mode="quick" title="Short, concise, minimal prose">Quick</button>
          <button type="button" class="mode-btn ${currentDetailMode === 'standard' ? 'active' : ''}" data-mode="standard" title="Balanced explanation with rich cards">Standard</button>
          <button type="button" class="mode-btn ${currentDetailMode === 'detailed' ? 'active' : ''}" data-mode="detailed" title="Comprehensive reasoning with full itinerary & accordions">Detailed</button>
        </div>
      </div>

      <!-- Quick Actions Toolbar -->
      <div class="quick-actions-bar">
        ${tenantConfig.has_packages !== false ? `
        <button type="button" class="action-pill-btn" id="btn-show-packages">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path></svg>
          <span>Packages</span>
        </button>
        <button type="button" class="action-pill-btn" id="btn-show-calc">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="2" width="16" height="20" rx="2"></rect><line x1="8" y1="6" x2="16" y2="6"></line><line x1="16" y1="14" x2="16" y2="18"></line><path d="M16 10h.01"></path><path d="M12 10h.01"></path><path d="M8 10h.01"></path><path d="M12 14h.01"></path><path d="M8 14h.01"></path><path d="M12 18h.01"></path><path d="M8 18h.01"></path></svg>
          <span>Trip Calculator</span>
        </button>
        ` : ''}
        ${tenantConfig.contact_phone ? `
          <a href="https://wa.me/${tenantConfig.contact_phone.replace(/[^0-9]/g, '')}?text=Hi%20${encodeURIComponent(tenantConfig.name)}" target="_blank" class="action-pill-btn" style="text-decoration:none;">
            <span>WhatsApp</span>
          </a>` : ''}
      </div>

      <!-- Messages Container -->
      <div class="messages-container" id="msg-feed">
        <div class="message-wrapper bot-wrapper">
          <div class="bot-bubble">
            ${renderFormattedText(tenantConfig.welcome_message || (tenantConfig.category === 'travel' ? 'Hello! Welcome to our travel concierge. How can we help plan your journey?' : 'Hello! How can I assist you today?'))}
          </div>
        </div>
        <button id="scroll-down-btn">Jump to latest</button>
      </div>

      <!-- Starter & Quick Reply Chips -->
      <div class="quick-replies" id="quick-feed">
        <!-- Rendered dynamically -->
      </div>

      <!-- Composer Input -->
      <form class="composer" id="chat-form">
        <button type="button" class="btn-icon" id="mic-btn" style="background:#f8fafc; border:1px solid #e2e8f0; color:#64748b;" title="Voice input" aria-label="Record voice">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z"></path><path d="M19 10v2a7 7 0 01-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>
        </button>
        <input type="text" class="chat-input" id="input-field" placeholder="${tenantConfig.category === 'travel' ? 'Ask about destinations, pricing, or itineraries...' : ((tenantConfig.category && (tenantConfig.category.includes('cricket') || tenantConfig.category.includes('sport'))) ? 'Ask about live scores, match schedules, player stats...' : 'Type your question here...')}" autocomplete="off" />
        <button type="submit" class="send-btn" id="send-btn">
          <span>Send</span>
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
        </button>
      </form>

      <div class="powered-by">
        Powered by <a href="https://devlancer.in" target="_blank">Devlancer</a> • Minimalist AI Engine
      </div>

      <!-- Cost Calculator Modal -->
      <div id="calc-overlay">
        <div class="calc-modal">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <h4>Trip Budget Estimator</h4>
            <button id="calc-close-btn" style="border:none; background:none; font-size:16px; cursor:pointer; color:#71717a;">&times;</button>
          </div>
          <label style="color:#71717a; font-size:11px;">Destination</label>
          <input id="calc-dest" class="calc-input" value="Europe Fixed Departure" />
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
            <div>
              <label style="color:#71717a; font-size:11px;">Adults (12+ yrs)</label>
              <input id="calc-adults" type="number" min="1" max="50" value="2" class="calc-input" />
            </div>
            <div>
              <label style="color:#71717a; font-size:11px;">Seniors (60+ yrs)</label>
              <input id="calc-seniors" type="number" min="0" max="50" value="0" class="calc-input" />
            </div>
          </div>
          <div class="calc-res-box">
            <span style="font-size:10.5px; color:#71717a;">Estimated Group Budget</span>
            <div class="calc-price" id="calc-total-inr">₹2,40,000</div>
            <span style="font-size:10px; color:#10b981;">Includes hotels, flights, meals & support</span>
          </div>
          <button id="calc-send-btn" class="send-btn" style="width:100%; justify-content:center; padding:9px; border-radius:8px;">
            Inquire for this Estimate
          </button>
        </div>
      </div>
    `;
    shadow.appendChild(win);

    // Bind DOM references
    const themeBtn = shadow.getElementById('theme-btn');
    const maxBtn = shadow.getElementById('max-btn');
    const closeBtn = shadow.getElementById('close-btn');
    const menuBtn = shadow.getElementById('menu-btn');
    const headerMenu = shadow.getElementById('header-menu');
    const form = shadow.getElementById('chat-form');
    const sendBtn = shadow.getElementById('send-btn');
    const inputField = shadow.getElementById('input-field');
    const msgFeed = shadow.getElementById('msg-feed');
    const quickFeed = shadow.getElementById('quick-feed');
    const micBtn = shadow.getElementById('mic-btn');
    const scrollDownBtn = shadow.getElementById('scroll-down-btn');
    const modeSwitcher = shadow.getElementById('mode-switcher');

    // Theme Switcher Logic (Dark vs Light)
    let currentTheme = 'light';
    try {
      const savedTheme = localStorage.getItem('devlancer_widget_theme');
      if (savedTheme) {
        currentTheme = savedTheme;
      } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        currentTheme = 'dark';
      }
    } catch (e) {}

    function applyTheme(theme) {
      currentTheme = theme;
      if (theme === 'dark') {
        win.classList.add('dark-theme');
        if (themeBtn) {
          themeBtn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`;
          themeBtn.setAttribute('title', 'Switch to Light Theme');
        }
      } else {
        win.classList.remove('dark-theme');
        if (themeBtn) {
          themeBtn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`;
          themeBtn.setAttribute('title', 'Switch to Dark Theme');
        }
      }
      try { localStorage.setItem('devlancer_widget_theme', theme); } catch (e) {}
    }
    applyTheme(currentTheme);

    if (themeBtn) {
      themeBtn.onclick = () => { applyTheme(currentTheme === 'dark' ? 'light' : 'dark'); };
    }
    const optThemeToggle = shadow.getElementById('opt-theme-toggle');
    if (optThemeToggle) {
      optThemeToggle.onclick = () => { applyTheme(currentTheme === 'dark' ? 'light' : 'dark'); };
    }

    // Calculator DOM references
    const calcOverlay = shadow.getElementById('calc-overlay');
    const calcCloseBtn = shadow.getElementById('calc-close-btn');
    const calcDest = shadow.getElementById('calc-dest');
    const calcAdults = shadow.getElementById('calc-adults');
    const calcSeniors = shadow.getElementById('calc-seniors');
    const calcTotalInr = shadow.getElementById('calc-total-inr');
    const calcSendBtn = shadow.getElementById('calc-send-btn');
    const btnShowCalc = shadow.getElementById('btn-show-calc');
    const btnShowPackages = shadow.getElementById('btn-show-packages');

    // Populate Initial Starter Prompts
    renderStarterPrompts();

    function renderStarterPrompts() {
      let prompts = tenantConfig.starter_prompts;
      if (!prompts || prompts.length === 0) {
        if (tenantConfig.category === 'travel') {
          prompts = ["Top Packages", "Plan a 5-Day Trip", "Senior Citizen Tours", "Cancellation Policies"];
        } else if (tenantConfig.category && tenantConfig.category.includes('cricket')) {
          prompts = ["Live Cricket Scores", "Upcoming Fixtures", "Recent Match Results", "Player Rankings"];
        } else if (tenantConfig.category && tenantConfig.category.includes('sport')) {
          prompts = ["Live Scores", "Schedule", "Top Teams", "Latest News"];
        } else {
          prompts = ["Overview", "Frequently Asked Questions", "Contact Support"];
        }
      }
      
      quickFeed.innerHTML = prompts.map(p => `
        <button class="quick-chip" data-text="${escapeHtml(p)}">${escapeHtml(p)}</button>
      `).join('');
    }

    // Toggle Chat Window
    function toggleChat() {
      isOpen = !isOpen;
      win.style.display = isOpen ? 'flex' : 'none';
      if (isOpen) {
        inputField.focus();
        msgFeed.scrollTop = msgFeed.scrollHeight;
      }
    }

    // Toggle Full-Screen
    maxBtn.onclick = () => {
      isMaximized = !isMaximized;
      if (isMaximized) {
        win.classList.add('maximized');
      } else {
        win.classList.remove('maximized');
      }
      setTimeout(() => { msgFeed.scrollTop = msgFeed.scrollHeight; }, 100);
    };

    closeBtn.onclick = toggleChat;

    // Menu toggle
    menuBtn.onclick = (e) => {
      e.stopPropagation();
      headerMenu.classList.toggle('active');
    };
    shadow.addEventListener('click', () => headerMenu.classList.remove('active'));

    // Mode Switcher Binding
    modeSwitcher.addEventListener('click', (e) => {
      const btn = e.target.closest('.mode-btn');
      if (!btn) return;
      const targetMode = btn.getAttribute('data-mode');
      if (targetMode === currentDetailMode) return;

      currentDetailMode = targetMode;
      modeSwitcher.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      // Dispatch backend mode update
      executeAction('set_detail_mode', { detail_mode: targetMode });
    });

    // Menu Actions
    shadow.getElementById('opt-new-chat').onclick = async () => {
      if (confirm("Reset conversation and start a fresh session?")) {
        try {
          await fetch(`${baseUrl}/api/chat/reset`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: SESSION_ID, tenant_id: tenantConfig.tenant_id })
          });
        } catch (e) {}
        msgFeed.innerHTML = `
          <div class="message-wrapper bot-wrapper">
            <div class="bot-bubble">
              ${renderFormattedText(tenantConfig.welcome_message || 'Hello! How can we assist your trip planning today?')}
            </div>
          </div>
        `;
        renderStarterPrompts();
      }
    };

    shadow.getElementById('opt-regenerate').onclick = async () => {
      headerMenu.classList.remove('active');
      await regenerateLastAnswer();
    };

    shadow.getElementById('opt-copy-chat').onclick = () => {
      const text = Array.from(msgFeed.querySelectorAll('.message-wrapper')).map(el => el.innerText).join('\n\n');
      navigator.clipboard.writeText(text);
      alert("Consultation transcript copied to clipboard.");
    };

    shadow.getElementById('opt-privacy').onclick = async () => {
      if (confirm("Permanently erase session conversation records now?")) {
        try {
          await fetch(`${baseUrl}/api/privacy/delete-session-data`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: SESSION_ID, assistant_id: tenantConfig.assistant_id })
          });
          alert("Session data successfully erased.");
        } catch (e) {
          alert("Request registered.");
        }
      }
    };

    // Scroll Down Detection
    msgFeed.addEventListener('scroll', () => {
      const distFromBottom = msgFeed.scrollHeight - msgFeed.scrollTop - msgFeed.clientHeight;
      scrollDownBtn.style.display = distFromBottom > 120 ? 'block' : 'none';
    });
    scrollDownBtn.onclick = () => {
      msgFeed.scrollTop = msgFeed.scrollHeight;
    };

    // Quick Replies Binding
    quickFeed.addEventListener('click', (e) => {
      const chip = e.target.closest('.quick-chip');
      if (!chip) return;
      const text = chip.getAttribute('data-text') || chip.textContent;
      sendUserMessage(text);
    });

    // Packages Toolbar Button
    if (btnShowPackages) {
      btnShowPackages.onclick = () => {
        const pkgs = tenantConfig.packages || [];
        if (pkgs.length === 0) {
          sendUserMessage("What holiday packages do you currently offer?");
          return;
        }
        const cardsData = pkgs.map(p => ({
          card_id: p.id || p.name,
          title: p.name,
          duration: p.duration,
          price: `₹${Number(p.starting_price_inr).toLocaleString('en-IN')}`,
          badge: p.category || "Tour",
          highlights: (p.highlights || '').split('.').map(s => s.trim()).filter(Boolean).slice(0, 3),
          actions: [{
            action_id: `inq_${p.name}`,
            label: "Inquire Now",
            action_type: "send_message",
            payload: { message: `I would like to inquire about the ${p.name} package.` }
          }]
        }));

        const wrap = document.createElement('div');
        wrap.className = 'message-wrapper bot-wrapper';
        wrap.innerHTML = `
          <div class="bot-bubble">
            <div class="ans-summary">Verified Tour Packages for ${escapeHtml(tenantConfig.name)}</div>
            ${renderCardsHtml(cardsData)}
          </div>
        `;
        msgFeed.appendChild(wrap);
        msgFeed.scrollTop = msgFeed.scrollHeight;
        bindActionButtons(wrap);
      };
    }

    // Calculator Logic
    if (btnShowCalc) {
      btnShowCalc.onclick = () => { calcOverlay.style.display = 'flex'; updateCalc(); };
    }
    calcCloseBtn.onclick = () => { calcOverlay.style.display = 'none'; };
    function updateCalc() {
      const adults = parseInt(calcAdults.value || 1, 10);
      const seniors = parseInt(calcSeniors.value || 0, 10);
      const basePerPerson = 120000;
      const seniorDiscount = 5000;
      const estimate = (adults * basePerPerson) + (seniors * (basePerPerson - seniorDiscount));
      calcTotalInr.textContent = `₹${estimate.toLocaleString('en-IN')}`;
    }
    calcAdults.oninput = updateCalc;
    calcSeniors.oninput = updateCalc;
    calcSendBtn.onclick = () => {
      const dest = calcDest.value;
      const adults = calcAdults.value;
      const seniors = calcSeniors.value;
      const total = calcTotalInr.textContent;
      calcOverlay.style.display = 'none';
      sendUserMessage(`Trip estimate: ${adults} adults and ${seniors} seniors for ${dest}. Estimated budget: ${total}. Please propose an itinerary and dates.`);
    };

    // Voice Speech-to-Text
    micBtn.onclick = () => {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRecognition) {
        alert("Voice speech recognition is not supported in this browser. Please use Chrome or Safari.");
        return;
      }
      if (isRecording && speechRec) {
        speechRec.stop();
        isRecording = false;
        micBtn.style.background = '#f8fafc';
        return;
      }
      speechRec = new SpeechRecognition();
      speechRec.lang = "en-IN";
      speechRec.continuous = false;
      speechRec.interimResults = true;
      speechRec.onstart = () => {
        isRecording = true;
        micBtn.style.background = '#fee2e2';
        micBtn.style.color = '#dc2626';
        inputField.placeholder = "Listening...";
      };
      speechRec.onresult = (ev) => {
        let t = "";
        for (let i = ev.resultIndex; i < ev.results.length; ++i) t += ev.results[i][0].transcript;
        inputField.value = t;
      };
      speechRec.onend = () => {
        isRecording = false;
        micBtn.style.background = '#f8fafc';
        micBtn.style.color = '#64748b';
        inputField.placeholder = "Ask about destinations, pricing, or itineraries...";
      };
      speechRec.start();
    };

    // Form Submit
    form.onsubmit = (e) => {
      e.preventDefault();
      const text = inputField.value.trim();
      if (!text) return;
      sendUserMessage(text);
    };

    // Send User Message
    async function sendUserMessage(text, executedAction = null) {
      inputField.value = '';
      sendBtn.disabled = true;
      
      const userWrap = document.createElement('div');
      userWrap.className = 'message-wrapper user-wrapper';
      userWrap.innerHTML = `<div class="user-bubble">${escapeHtml(text)}</div>`;
      msgFeed.appendChild(userWrap);
      msgFeed.scrollTop = msgFeed.scrollHeight;

      // Typing indicator with animated dots
      const typingWrap = document.createElement('div');
      typingWrap.className = 'message-wrapper bot-wrapper';
      typingWrap.id = 'typing-el';
      typingWrap.innerHTML = `
        <div class="bot-bubble" style="display: inline-flex; align-items: center; gap: 8px; padding: 9px 12px;">
          <div class="typing-dots">
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
          </div>
          <span style="color: #71717a; font-size: 11.5px; font-weight: 500;">${tenantConfig.category === 'travel' ? 'Consulting travel desk...' : 'Consulting assistant...'}</span>
        </div>
      `;
      msgFeed.appendChild(typingWrap);
      msgFeed.scrollTop = msgFeed.scrollHeight;

      try {
        const recentHistory = conversationHistory.slice(-4);
        const payload = {
          assistant_id: assistantId || tenantConfig.assistant_id,
          session_id: SESSION_ID,
          message: text,
          detail_mode: currentDetailMode,
          action: executedAction,
          domain: tenantConfig.domain || window.location.hostname,
          history: recentHistory
        };

        const res = await fetch(`${baseUrl}/api/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        const data = await res.json();
        const typingEl = shadow.getElementById('typing-el');
        if (typingEl) typingEl.remove();
        sendBtn.disabled = false;

        if (!res.ok) {
          appendBotMessageText(`Notice: ${data.detail || 'Service currently unavailable'}`);
          return;
        }

        // Maintain in-memory client history (Stateless - Never saved to DB)
        conversationHistory.push({ role: 'user', text: text });
        conversationHistory.push({ role: 'model', text: data.reply_message || data.reply || '' });
        if (conversationHistory.length > 8) conversationHistory = conversationHistory.slice(-8);

        // Render full rich structured response
        renderRichBotResponse(data);

        // Update dynamic quick replies
        if (data.quick_replies && data.quick_replies.length > 0) {
          quickFeed.innerHTML = data.quick_replies.map(qr => `
            <button class="quick-chip" data-text="${escapeHtml(qr)}">${escapeHtml(qr)}</button>
          `).join('');
        }

      } catch (err) {
        const typingEl = shadow.getElementById('typing-el');
        if (typingEl) typingEl.remove();
        sendBtn.disabled = false;
        appendBotMessageText("Connection error. Please check your network and try again.");
      }
    }

    // Regenerate last response in current detail mode
    async function regenerateLastAnswer() {
      const typingWrap = document.createElement('div');
      typingWrap.className = 'message-wrapper bot-wrapper';
      typingWrap.id = 'typing-el';
      typingWrap.innerHTML = `<div class="bot-bubble" style="color: #71717a; font-style: italic;">Regenerating response in ${currentDetailMode} mode...</div>`;
      msgFeed.appendChild(typingWrap);
      msgFeed.scrollTop = msgFeed.scrollHeight;

      try {
        const res = await fetch(`${baseUrl}/api/chat/regenerate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: SESSION_ID,
            assistant_id: tenantConfig.assistant_id,
            detail_mode: currentDetailMode
          })
        });
        const data = await res.json();
        const typingEl = shadow.getElementById('typing-el');
        if (typingEl) typingEl.remove();

        if (res.ok) {
          renderRichBotResponse(data);
        }
      } catch (e) {
        const typingEl = shadow.getElementById('typing-el');
        if (typingEl) typingEl.remove();
      }
    }

    // =================================================================
    // 4. ACTION ENGINE DISPATCHER
    // =================================================================
    async function executeAction(actionType, payload = {}) {
      try {
        // Handle client-side immediate actions
        if (actionType === 'set_detail_mode') {
          await fetch(`${baseUrl}/api/action/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              session_id: SESSION_ID,
              assistant_id: tenantConfig.assistant_id,
              action_type: 'set_detail_mode',
              payload: payload
            })
          });
          return;
        }

        if (actionType === 'submit_enquiry_confirm') {
          const res = await fetch(`${baseUrl}/api/action/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              session_id: SESSION_ID,
              assistant_id: tenantConfig.assistant_id,
              action_type: 'submit_enquiry_confirm',
              payload: payload
            })
          });
          const d = await res.json();
          appendBotMessageText(d.message || "Thank you! Your travel inquiry has been confirmed with our team.");
          return;
        }

        // For conversational triggers (compare, start_itinerary, send_message)
        const msg = payload.message || (actionType === 'compare_packages' ? 'Compare top packages' : 'Tell me more');
        sendUserMessage(msg, { action_type: actionType, payload: payload });
      } catch (err) {
        console.error("Action execution error:", err);
      }
    }

    // =================================================================
    // 5. RICH RESPONSE RENDERING ENGINE
    // =================================================================
    function renderRichBotResponse(data) {
      const wrap = document.createElement('div');
      wrap.className = 'message-wrapper bot-wrapper';
      const msgId = "msg_" + Math.random().toString(36).substring(2, 8);

      const comps = data.components || {};
      let html = '';

      // A. Bot Message Meta (Site Logo + Name)
      html += `
        <div class="bot-msg-meta">
          <div class="bot-msg-avatar">
            ${logoUrl ? `
              <img src="${escapeHtml(logoUrl)}" alt="" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" />
              <span class="avatar-initial" style="display:none;">${initial}</span>
            ` : `
              <span class="avatar-initial">${initial}</span>
            `}
          </div>
          <span class="bot-msg-sender">${escapeHtml(tenantConfig.assistant_name || tenantConfig.name || 'Assistant')}</span>
        </div>
      `;

      // B. Answer Summary
      if (comps.summary) {
        html += `<div class="ans-summary">${escapeHtml(comps.summary)}</div>`;
      }

      // B. Main Conversational Reply Text & Client-Side JSON Stripper
      if (data.reply) {
        let cleanReply = data.reply;
        // Clean out any raw JSON blocks that might have leaked
        const jsonMatch = cleanReply.match(/(\{[\s\S]*\"(?:format_style|cards)\"[\s\S]*\})/);
        if (jsonMatch) {
          try {
            const parsedEmbedded = JSON.parse(jsonMatch[1]);
            if ((!comps.cards || comps.cards.length === 0) && parsedEmbedded.cards) {
              comps.cards = parsedEmbedded.cards;
            }
          } catch(e) {}
          cleanReply = (cleanReply.substring(0, jsonMatch.index) + cleanReply.substring(jsonMatch.index + jsonMatch[0].length)).trim();
        }
        cleanReply = cleanReply.replace(/```(?:json)?[\s\S]*?```/g, '').trim();

        if (cleanReply) {
          html += `<div class="reply-text">${renderFormattedText(cleanReply)}</div>`;
        }
      }

      // C. Information Cards
      if (comps.cards && comps.cards.length > 0) {
        html += renderCardsHtml(comps.cards);
      }

      // D. Comparison Table
      if (comps.comparison_table) {
        html += renderComparisonTableHtml(comps.comparison_table);
      }

      // E. Day-by-Day Itinerary
      if (comps.itinerary && comps.itinerary.length > 0) {
        html += renderItineraryHtml(comps.itinerary);
      }

      // F. Step-by-Step Instructions
      if (comps.steps && comps.steps.length > 0) {
        html += renderStepsHtml(comps.steps);
      }

      // G. Expandable Accordions
      if (comps.accordions && comps.accordions.length > 0) {
        html += renderAccordionsHtml(comps.accordions);
      }

      // H. Interactive Checklists
      if (comps.checklists && comps.checklists.length > 0) {
        html += renderChecklistsHtml(comps.checklists);
      }

      // I. Budget Breakdown
      if (comps.budget_breakdown) {
        html += renderBudgetBreakdownHtml(comps.budget_breakdown);
      }

      // J. Verified Source Citations
      if (comps.source_references && comps.source_references.length > 0) {
        html += renderSourcesHtml(comps.source_references);
      }

      // K. Smart Follow-Up Question with Chips
      if (comps.follow_up) {
        html += renderFollowUpHtml(comps.follow_up);
      }

      // L. Contextual Action Buttons
      if (comps.suggested_actions && comps.suggested_actions.length > 0) {
        html += renderActionsHtml(comps.suggested_actions);
      }

      // M. Explicit Enquiry Confirmation Prompt (if phone detected and unconfirmed)
      if (data.lead_state && data.lead_state.phone_number && !data.crm_synced_now) {
        html += renderConfirmationCardHtml(data.lead_state);
      }

      // Footer Meta & Action Links
      html += `
        <div class="msg-actions">
          <span>${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} • ${escapeHtml(tenantConfig.assistant_name || 'Concierge')}</span>
          <div class="action-btns">
            <span class="action-link" id="copy-${msgId}">Copy</span>
            ${'speechSynthesis' in window ? `<span class="action-link" id="listen-${msgId}">Listen</span>` : ''}
            <span class="feedback-btn" id="up-${msgId}" title="Helpful">👍</span>
            <span class="feedback-btn" id="down-${msgId}" title="Improve">👎</span>
          </div>
        </div>
      `;

      wrap.innerHTML = `<div class="bot-bubble">${html}</div>`;
      msgFeed.appendChild(wrap);
      msgFeed.scrollTop = msgFeed.scrollHeight;

      // Bind dynamic actions inside this bubble
      bindActionButtons(wrap);

      // Copy text binding
      shadow.getElementById(`copy-${msgId}`).onclick = function() {
        navigator.clipboard.writeText(data.reply || '');
        this.textContent = "Copied";
        setTimeout(() => this.textContent = "Copy", 1800);
      };

      // TTS Audio binding
      if ('speechSynthesis' in window) {
        shadow.getElementById(`listen-${msgId}`).onclick = function() {
          if (window.speechSynthesis.speaking) {
            window.speechSynthesis.cancel();
            this.textContent = "Listen";
          } else {
            const u = new SpeechSynthesisUtterance((data.reply || '').replace(/[|*#_]/g, ' '));
            u.lang = "en-IN";
            u.onend = () => this.textContent = "Listen";
            window.speechSynthesis.speak(u);
            this.textContent = "Stop";
          }
        };
      }

      // Feedback Thumbs binding
      shadow.getElementById(`up-${msgId}`).onclick = function() {
        this.classList.add('active');
        recordFeedback("up");
      };
      shadow.getElementById(`down-${msgId}`).onclick = function() {
        this.classList.add('active');
        recordFeedback("down");
      };
    }

    // HTML Generator Helpers
    function renderCardsHtml(cards) {
      return `
        <div class="ans-cards-grid">
          ${cards.map(c => `
            <div class="info-card">
              <div>
                ${c.badge ? `<span class="card-badge">${escapeHtml(c.badge)}</span>` : ''}
                <div class="card-title">${escapeHtml(c.title)}</div>
                ${c.duration ? `<div class="card-duration">${escapeHtml(c.duration)}</div>` : ''}
                ${c.price ? `<div class="card-price">${escapeHtml(c.price)}</div>` : ''}
                ${c.highlights && c.highlights.length > 0 ? `
                  <ul class="card-highlights">
                    ${c.highlights.map(h => `<li>${escapeHtml(h)}</li>`).join('')}
                  </ul>` : ''}
              </div>
              <div class="card-actions">
                ${(c.actions || []).map(act => `
                  <button type="button" class="action-btn" data-action="${escapeHtml(JSON.stringify(act))}">
                    ${escapeHtml(act.label)}
                  </button>
                `).join('')}
              </div>
            </div>
          `).join('')}
        </div>
      `;
    }

    function renderComparisonTableHtml(table) {
      return `
        <div class="comp-table-wrap">
          <table class="comp-table">
            <thead>
              <tr>
                ${table.headers.map(h => `<th>${escapeHtml(h)}</th>`).join('')}
              </tr>
            </thead>
            <tbody>
              ${table.rows.map(row => `
                <tr>
                  ${row.map(cell => `<td>${escapeHtml(cell)}</td>`).join('')}
                </tr>
              `).join('')}
            </tbody>
          </table>
          ${table.highlights ? `<div class="comp-highlights-footer"><strong>Summary:</strong> ${escapeHtml(table.highlights)}</div>` : ''}
        </div>
      `;
    }

    function renderItineraryHtml(days) {
      return `
        <div class="itinerary-timeline">
          ${days.map(d => `
            <div class="itinerary-day">
              <span class="day-marker"></span>
              <div class="day-heading">Day ${d.day_number}: ${escapeHtml(d.title)}</div>
              ${d.morning ? `<div class="day-block"><strong>Morning:</strong> ${escapeHtml(d.morning)}</div>` : ''}
              ${d.afternoon ? `<div class="day-block"><strong>Afternoon:</strong> ${escapeHtml(d.afternoon)}</div>` : ''}
              ${d.evening ? `<div class="day-block"><strong>Evening:</strong> ${escapeHtml(d.evening)}</div>` : ''}
              ${d.meal_stay ? `<span class="day-tag">${escapeHtml(d.meal_stay)}</span>` : ''}
              ${d.notes ? `<div style="font-size:10px; color:#71717a; margin-top:2px;"><em>Tip: ${escapeHtml(d.notes)}</em></div>` : ''}
            </div>
          `).join('')}
        </div>
      `;
    }

    function renderStepsHtml(steps) {
      return `
        <div class="steps-box">
          ${steps.map(s => `
            <div class="step-row">
              <span class="step-badge">${s.step_number}</span>
              <div class="step-text">
                <strong>${escapeHtml(s.title)}</strong>
                <span>${escapeHtml(s.description)}</span>
              </div>
            </div>
          `).join('')}
        </div>
      `;
    }

    function renderAccordionsHtml(accordions) {
      return `
        <div class="accordion-group">
          ${accordions.map(a => `
            <details class="ans-accordion" ${a.default_expanded ? 'open' : ''}>
              <summary>
                <span>${escapeHtml(a.title)}</span>
                <span style="font-size:10px; color:#71717a;">▼</span>
              </summary>
              <div class="ans-accordion-body">${renderFormattedText(a.content)}</div>
            </details>
          `).join('')}
        </div>
      `;
    }

    function renderChecklistsHtml(checklists) {
      return `
        <div>
          ${checklists.map(grp => `
            <div class="checklist-card">
              <div class="checklist-title">${escapeHtml(grp.category)}</div>
              ${grp.items.map(item => `
                <label class="check-item">
                  <input type="checkbox" />
                  <span>${escapeHtml(item)}</span>
                </label>
              `).join('')}
            </div>
          `).join('')}
        </div>
      `;
    }

    function renderBudgetBreakdownHtml(b) {
      return `
        <div class="budget-card">
          <div style="font-size:11px; font-weight:700; color:#0f172a; margin-bottom:6px;">Itemized Budget Breakdown (${escapeHtml(b.currency || 'INR')})</div>
          ${(b.items || []).map(i => `
            <div class="budget-row">
              <span>${escapeHtml(i.item)}</span>
              <span><strong>${escapeHtml(i.cost)}</strong> ${i.is_estimate ? '<em style="font-size:9.5px; color:#71717a;">(Est.)</em>' : '<span style="font-size:9px; color:#10b981;">✓ Fixed</span>'}</span>
            </div>
          `).join('')}
          ${b.confirmed_total || b.estimated_total ? `
            <div class="budget-total-row">
              <span>Estimated Total:</span>
              <span>${escapeHtml(b.estimated_total || b.confirmed_total)}</span>
            </div>
          ` : ''}
          ${b.disclaimer ? `<div style="font-size:9.5px; color:#94a3b8; margin-top:4px;">* ${escapeHtml(b.disclaimer)}</div>` : ''}
        </div>
      `;
    }

    function renderSourcesHtml(sources) {
      return `
        <div class="sources-box">
          ${sources.map(s => `
            <span class="source-chip" title="${escapeHtml(s.quote || '')}">
              <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>
              <span>${escapeHtml(s.title)}</span>
            </span>
          `).join('')}
        </div>
      `;
    }

    function renderFollowUpHtml(f) {
      return `
        <div class="followup-box">
          <div class="followup-q">${escapeHtml(f.question)}</div>
          <div class="followup-chips">
            ${(f.chips || []).map(chip => `
              <button type="button" class="chip-btn" data-chip="${escapeHtml(chip)}">${escapeHtml(chip)}</button>
            `).join('')}
          </div>
        </div>
      `;
    }

    function renderActionsHtml(actions) {
      return `
        <div class="actions-container">
          ${actions.map((act, idx) => `
            <button type="button" class="action-btn ${idx > 0 ? 'secondary' : ''}" data-action="${escapeHtml(JSON.stringify(act))}">
              <span>${escapeHtml(act.label)}</span>
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"></path></svg>
            </button>
          `).join('')}
        </div>
      `;
    }

    function renderConfirmationCardHtml(lead) {
      return `
        <div class="confirm-enquiry-card">
          <h5>Confirm Travel Inquiry</h5>
          <p>Would you like us to submit your details to the official ${escapeHtml(tenantConfig.name)} tour manager desk?</p>
          <div class="confirm-details">
            Name: ${escapeHtml(lead.customer_name || 'Website Traveler')}<br/>
            Phone: ${escapeHtml(lead.phone_number)}<br/>
            Destination: ${escapeHtml(lead.destination_interest || 'General Tour')}
          </div>
          <div class="confirm-btns">
            <button type="button" class="action-btn" data-action='{"action_type":"submit_enquiry_confirm","payload":${JSON.stringify(lead)}}'>
              ✓ Confirm & WhatsApp Itinerary
            </button>
          </div>
        </div>
      `;
    }

    function bindActionButtons(container) {
      // Bind follow-up chips
      container.querySelectorAll('.chip-btn').forEach(btn => {
        btn.onclick = () => {
          const chipVal = btn.getAttribute('data-chip');
          sendUserMessage(chipVal);
        };
      });

      // Bind action buttons
      container.querySelectorAll('.action-btn').forEach(btn => {
        btn.onclick = () => {
          const raw = btn.getAttribute('data-action');
          if (!raw) return;
          try {
            const act = JSON.parse(raw);
            executeAction(act.action_type, act.payload || {});
          } catch (e) {
            console.error("Action parse error:", e);
          }
        };
      });
    }

    function appendBotMessageText(text) {
      renderRichBotResponse({ reply: text, components: {} });
    }

    async function recordFeedback(rating) {
      try {
        await fetch(`${baseUrl}/api/feedback`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: SESSION_ID, assistant_id: tenantConfig.assistant_id, rating: rating })
        });
      } catch (e) {}
    }

    // Markdown Parser (Headers, bold, lists, and GFM Tables)
    function renderFormattedText(raw) {
      if (!raw) return '';
      let text = raw;

      // Tables
      text = text.replace(/((?:\|[^\n]+\|\r?\n)+)/g, function (match) {
        const lines = match.trim().split('\n').map(l => l.trim()).filter(l => l.startsWith('|'));
        if (lines.length < 2) return match;
        
        let html = '<div style="overflow-x:auto; margin:6px 0;"><table class="comp-table">';
        let isHeader = true;
        for (let i = 0; i < lines.length; i++) {
          if (lines[i].includes('---')) {
            isHeader = false;
            continue;
          }
          const cells = lines[i].split('|').slice(1, -1).map(c => c.trim());
          html += '<tr>';
          for (let cell of cells) {
            html += isHeader ? `<th>${cell}</th>` : `<td>${cell}</td>`;
          }
          html += '</tr>';
          if (isHeader) isHeader = false;
        }
        html += '</table></div>';
        return html;
      });

      // Markdown formatting
      text = text
        .replace(/^### (.*$)/gim, '<div style="font-weight:600; font-size:12px; margin:4px 0 2px 0;">$1</div>')
        .replace(/^## (.*$)/gim, '<div style="font-weight:700; font-size:12.5px; margin:5px 0 2px 0;">$1</div>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/^\s*[-•]\s+(.*)$/gim, '<li style="margin-left:14px; font-size:11.5px; margin-bottom:2px;">$1</li>')
        .replace(/\n\n/g, '<div style="height:6px;"></div>')
        .replace(/\n/g, '<br/>');

      return text;
    }
  }

  // Load config on boot
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', fetchConfig);
  } else {
    fetchConfig();
  }

})();
