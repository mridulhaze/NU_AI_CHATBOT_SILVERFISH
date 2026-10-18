# 🔌 National University AI Assistant — Embeddable Chat Widget Guide

The NU AI Assistant provides a lightweight, dependency-free JavaScript widget that can be embedded on any external website, affiliate college portal, or LMS.

---

## 🚀 1. Quick Integration

Add this single script tag before the closing `</body>` tag on your website:

```html
<!-- National University AI Chat Widget -->
<script src="https://YOUR-AI-DOMAIN/static/nu-chat-widget.js" defer></script>
```

When loaded locally:
```html
<script src="http://127.0.0.1:8000/static/nu-chat-widget.js" defer></script>
```

---

## 🎨 2. Configuration Attributes

You can customize the widget title and primary accent color using HTML `data-*` attributes:

```html
<script 
  src="http://127.0.0.1:8000/static/nu-chat-widget.js" 
  data-title="NU Academic Helpdesk"
  data-color="#047857"
  defer>
</script>
```

| Attribute | Default | Description |
|---|---|---|
| `data-title` | `জাতীয় বিশ্ববিদ্যালয় এআই কাউন্সেলর` | Header title of the widget |
| `data-color` | `#047857` (Emerald 700) | Primary branding color of the button & header |

---

## 🔒 3. Security & Privacy Safeguards

1. **Zero Secret Exposure**: The widget never requires or exposes `GEMINI_API_KEY` or JWT tokens in client-side code.
2. **Server-Side Validation**: All queries are sanitized and rate-limited per IP (`backend/rate_limiter.py`).
3. **Restricted Scope**: The widget iframe routes to `/chat`, which only serves the public student chat interface. All administrative tabs, token solver workspaces, and crawler controls are strictly inaccessible.
4. **CORS Protected**: Standard cross-origin headers allow iframe embedding while disallowing unauthorized REST modification of internal endpoints.

---

## 💻 4. Interactive Live Demo

To test the widget locally, visit:
**`http://127.0.0.1:8000/embed-demo.html`** or **`http://127.0.0.1:8000/demo`**.