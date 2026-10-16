"""Generate the page's diagrams in both languages: <name>.svg (en) and <name>.vi.svg (vi)."""
from pathlib import Path

OUT = Path(__file__).parent


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Svg:
    def __init__(self, name, w, h, title, desc):
        self.name, self.w, self.h = name, w, h
        self.parts = []
        self.title, self.desc = title, desc

    def add(self, s):
        self.parts.append(s)

    def band(self, x, y, w, h, label=None, cls="band"):
        self.add(f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="12"/>')
        if label:
            self.add(f'<text class="t-h" x="{x + 12}" y="{y + 18}">{esc(label)}</text>')

    def box(self, x, y, w, h, title, sub=None, cls="n-box", tcls="t t-b"):
        self.add(f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/>')
        cx = x + w / 2
        if sub:
            self.add(f'<text class="{tcls}" x="{cx}" y="{y + h / 2 - 9}" text-anchor="middle" dominant-baseline="central">{esc(title)}</text>')
            self.add(f'<text class="t-s" x="{cx}" y="{y + h / 2 + 10}" text-anchor="middle" dominant-baseline="central">{esc(sub)}</text>')
        else:
            self.add(f'<text class="{tcls}" x="{cx}" y="{y + h / 2}" text-anchor="middle" dominant-baseline="central">{esc(title)}</text>')

    def line(self, x1, y1, x2, y2, cls="w", arrow=True):
        m = f' marker-end="url(#{self.name}-ah)"' if arrow else ""
        self.add(f'<line class="{cls}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"{m}/>')

    def path(self, d, cls="w", arrow=True):
        m = f' marker-end="url(#{self.name}-ah)"' if arrow else ""
        self.add(f'<path class="{cls}" d="{d}"{m}/>')

    def text(self, x, y, s, cls="t-s", anchor="middle"):
        self.add(f'<text class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}" dominant-baseline="central">{esc(s)}</text>')

    def render(self, suffix):
        tid = f"{self.name}{suffix.replace('.', '-')}-t"
        head = (
            f'<svg viewBox="0 0 {self.w} {self.h}" role="img" aria-labelledby="{tid}">'
            f'<title id="{tid}">{esc(self.title)}</title><desc>{esc(self.desc)}</desc>'
            f'<defs><marker id="{self.name}-ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" '
            f'markerHeight="6" orient="auto-start-reverse"><path d="M2 1L8 5L2 9z" fill="var(--ink-3)"/></marker></defs>'
        )
        return head + "".join(self.parts) + "</svg>\n"


def both(fn):
    for lang, suffix in (("en", ""), ("vi", ".vi")):
        s = fn(lang)
        # Marker ids must differ between the two language versions, which can sit on one page.
        body = s.render(suffix).replace(f"#{s.name}-ah", f"#{s.name}{suffix.replace('.', '-')}-ah").replace(
            f'id="{s.name}-ah"', f'id="{s.name}{suffix.replace(".", "-")}-ah"')
        (OUT / f"{s.name}{suffix}.svg").write_text(body)


def L(lang, en, vi):
    return vi if lang == "vi" else en


# 1 — Layers, the abstract picture --------------------------------------------------------------
def layers(lang):
    s = Svg("pt-layers", 680, 470,
            L(lang, "Five layers from the person to the AI agent", "Năm tầng từ con người đến AI agent"),
            L(lang, "Surfaces, web edge, core API with stores, host bridge, AI agents.",
              "Giao diện, web edge, API lõi và kho dữ liệu, cầu nối máy host, AI agent."))
    rows = [
        (L(lang, "1 · SURFACES", "1 · GIAO DIỆN"), [("PWA", L(lang, "browser, phone", "trình duyệt, điện thoại")),
                                                ("Raycast", L(lang, "hotkey actions", "phím tắt")),
                                                ("Terminal", "tmux attach -r")]),
        (L(lang, "2 · WEB EDGE", "2 · WEB EDGE"), [("Next.js 16 :7777", L(lang, "routes, /api/gql proxy, /raycast/*", "route, proxy /api/gql, /raycast/*"))]),
        (L(lang, "3 · CORE API", "3 · API LÕI"), [("Django GraphQL :8888", L(lang, "Module catalog, engines", "danh mục Module, các engine")),
                                                ("Postgres", L(lang, "durable", "bền vững")),
                                                ("Redis", L(lang, "live: pub/sub, lease", "live: pub/sub, lease"))]),
        (L(lang, "4 · HOST BRIDGE", "4 · CẦU NỐI HOST"), [("host-shim :9876", "HTTP → CLI"),
                                                     ("phantinh-bridge", L(lang, "bash CLI, one JSON line", "bash CLI, một dòng JSON"))]),
        (L(lang, "5 · AI AGENTS", "5 · AI AGENT"), [("claude TUI in tmux", L(lang, "interactive chat", "chat tương tác")),
                                                  ("claude -p / codex exec", L(lang, "one-shot, JSON schema", "oneshot, JSON schema"))]),
    ]
    y = 14
    centers = []
    for i, (label, boxes) in enumerate(rows):
        s.band(10, y, 660, 78, label)
        n = len(boxes)
        gap = 14
        x0, wtot = 178, 482
        bw = (wtot - gap * (n - 1)) / n
        for j, (t, sub) in enumerate(boxes):
            cls = "n-new" if (i == 2 and j == 0) else "n-box"
            s.box(x0 + j * (bw + gap), y + 13, bw, 52, t, sub, cls)
        centers.append(y)
        y += 92
    for i in range(len(rows) - 1):
        s.line(419, centers[i] + 65, 419, centers[i + 1] + 11)
    return s


# 2 — Deployment: host vs Docker -----------------------------------------------------------------
def deploy(lang):
    s = Svg("pt-deploy", 680, 430,
            L(lang, "What runs on the Mac host and what runs in Docker", "Cái gì chạy trên máy host, cái gì chạy trong Docker"),
            L(lang, "The API container cannot drive host tmux, so it calls a small HTTP shim on the host.",
              "Container API không điều khiển được tmux của host, nên gọi một HTTP shim nhỏ trên host."))
    s.band(10, 10, 660, 196, L(lang, "HOST · macOS (process-compose)", "HOST · macOS (process-compose)"))
    s.box(26, 38, 150, 50, "Next.js web", ":7777")
    s.box(196, 38, 150, 50, "host-shim.py", "127.0.0.1:9876", "n-new")
    s.box(366, 38, 140, 50, "phantinh-bridge", "bash CLI")
    s.box(526, 38, 130, 50, "tmux server", "phantinh-<id>")
    s.box(366, 120, 140, 66, "claude -p", L(lang, "codex exec · no tmux", "codex exec · không tmux"))
    s.box(526, 120, 130, 66, "claude TUI", L(lang, "writes JSONL", "ghi JSONL"))
    s.box(196, 120, 150, 66, L(lang, "Host-only tools", "Công cụ chỉ có trên host"), "keychain, git, pandoc, say")
    s.line(346, 63, 364, 63)
    s.line(506, 63, 524, 63)
    s.line(591, 88, 591, 118)
    s.line(436, 88, 436, 118)
    s.band(10, 220, 660, 200, L(lang, "DOCKER · compose project phantinh", "DOCKER · compose project phantinh"))
    s.box(26, 250, 200, 56, "api", L(lang, "uvicorn · Django + Strawberry", "uvicorn · Django + Strawberry"), "n-new")
    s.box(246, 250, 130, 56, "db", "Postgres 16 :5555")
    s.box(396, 250, 130, 56, "redis", "Redis 7 :6666")
    s.box(26, 330, 290, 72, L(lang, "3 loop containers", "3 container vòng lặp"), "reaper 600s · sync 3600s · mustwin 30s")
    s.box(336, 330, 320, 72, L(lang, "Read-only mounts", "Mount chỉ đọc"),
          L(lang, "bridge code, Claude config, skills, gallery", "code bridge, cấu hình Claude, skill, gallery"))
    s.line(226, 270, 244, 270)
    s.path("M226 294 L236 294 L236 316 L461 316 L461 308")
    s.path("M186 248 L186 104 L271 104 L271 90", cls="w-acc")
    s.text(192, 213, "HTTP → host.docker.internal:9876", "t-m", "start")
    s.line(60, 88, 60, 248, cls="w-dash")
    s.text(66, 112, "/api/gql", "t-m", "start")
    return s


# 3 — The chat loop -------------------------------------------------------------------------------
def chat(lang):
    s = Svg("pt-chat", 680, 330,
            L(lang, "A chat message goes out by paste and comes back through the transcript",
              "Tin nhắn đi bằng paste vào tmux và quay về qua transcript JSONL"),
            L(lang, "Outbound: mutation, shim, bridge send, tmux paste. Inbound: JSONL tail, tailer, Redis and Postgres, WebSocket.",
              "Chiều đi: mutation, shim, bridge send, paste vào tmux. Chiều về: tail JSONL, tailer, Redis và Postgres, WebSocket."))
    s.text(20, 22, L(lang, "OUTBOUND", "CHIỀU ĐI"), "t-h", "start")
    top = [("Browser", "sendMessage"), ("api", L(lang, "Message row", "dòng Message")),
           ("host-shim", "POST /run"), ("bridge send", "paste-buffer"), ("claude TUI", "tmux pane")]
    bw, gap, x0 = 116, 20, 14
    for i, (t, sub) in enumerate(top):
        s.box(x0 + i * (bw + gap), 38, bw, 54, t, sub, "n-new" if i == 4 else "n-box")
        if i:
            s.line(x0 + i * (bw + gap) - gap, 65, x0 + i * (bw + gap) - 2, 65)
    s.text(20, 152, L(lang, "INBOUND", "CHIỀU VỀ"), "t-h", "start")
    bot = [("Browser", "graphql-ws"), ("subscription", "sessionStream"),
           ("tailer", L(lang, "1 task / session", "1 task / session")), ("bridge tail", "tail -F → NDJSON"),
           ("JSONL", L(lang, "transcript file", "file transcript"))]
    for i, (t, sub) in enumerate(bot):
        s.box(x0 + i * (bw + gap), 168, bw, 54, t, sub, "n-ok" if i == 4 else "n-box")
        if i:
            s.line(x0 + i * (bw + gap) - 2, 195, x0 + i * (bw + gap) - gap, 195)
    last = x0 + 4 * (bw + gap) + bw / 2
    s.line(last, 92, last, 166)
    s.text(last + 8, 129, L(lang, "writes", "ghi"), "t-m", "start")
    tail_x = x0 + 2 * (bw + gap) + bw / 2
    sub_x = x0 + 1 * (bw + gap) + bw / 2
    s.box(sub_x - 70, 254, 140, 50, "Redis publish", L(lang, "live viewers", "người đang xem"))
    s.box(tail_x + 50, 254, 160, 50, "Postgres", L(lang, "Message, Report, cursor", "Message, Report, cursor"))
    s.path(f"M{tail_x - 14} 224 L{tail_x - 14} 279 L{sub_x + 72} 279")
    s.path(f"M{tail_x + 14} 224 L{tail_x + 14} 279 L{tail_x + 48} 279")
    s.line(sub_x, 254, sub_x, 224)
    return s


# 4 — Session lifecycle -----------------------------------------------------------------------------
def states(lang):
    s = Svg("pt-states", 680, 300,
            L(lang, "Session states and who moves them", "Trạng thái session và ai chuyển chúng"),
            L(lang, "Spawn moves provisioning to active; close, the reaper or a dead tmux end it; an idle close can revive.",
              "Spawn chuyển provisioning sang active; close, reaper hoặc tmux chết kết thúc; đóng vì idle có thể hồi lại."))
    s.box(20, 110, 130, 56, "provisioning", L(lang, "row created", "đã tạo dòng"))
    s.box(270, 110, 130, 56, "active", L(lang, "tailer running", "tailer đang chạy"), "n-new")
    s.box(520, 110, 140, 56, "closed", "close_reason", "n-ok")
    s.box(20, 222, 130, 50, "error", L(lang, "spawn / run failed", "spawn / chạy lỗi"), "n-bad")
    s.box(270, 222, 130, 50, "lost", L(lang, "DB row, no tmux", "có dòng DB, mất tmux"), "n-warn")
    s.line(150, 138, 268, 138)
    s.text(209, 126, "spawn ok", "t-m")
    s.line(400, 130, 518, 130)
    s.text(459, 100, "close · tmux_gone", "t-m")
    s.text(459, 116, "idle_ttl", "t-m")
    s.path("M520 156 C470 190 430 190 400 160")
    s.text(412, 200, L(lang, "revive: idle_ttl + tmux alive", "hồi lại: idle_ttl + tmux còn"), "t-m", "start")
    s.line(85, 166, 85, 220)
    s.text(92, 194, L(lang, "bridge error", "lỗi bridge"), "t-m", "start")
    s.line(335, 166, 335, 220)
    s.text(328, 194, "reconcileSessions", "t-m", "end")
    s.path("M85 110 C85 40 590 40 590 108")
    s.text(337, 50, L(lang, "oneshot done · or reaper: provisioning_timeout (no lease)",
                      "oneshot xong · hoặc reaper: provisioning_timeout (không còn lease)"), "t-m")
    return s


# 5 — Module dispatch -------------------------------------------------------------------------------
def dispatch(lang):
    s = Svg("pt-dispatch", 680, 360,
            L(lang, "A module is data; its kind picks the code", "Module là dữ liệu; kind chọn code chạy nó"),
            L(lang, "YAML seeds the Module row once; the row's kind selects the web workflow and the backend engine.",
              "YAML seed dòng Module một lần; kind của dòng chọn workflow ở web và engine ở backend."))
    s.box(20, 20, 150, 56, "modules/*.yaml", L(lang, "seed, insert-only", "seed, chỉ insert"))
    s.box(260, 20, 160, 56, "Module row", L(lang, "source of truth", "nguồn sự thật"), "n-new")
    s.box(510, 20, 150, 56, "/admin/settings", L(lang, "edits the row", "sửa dòng"))
    s.line(170, 48, 258, 48)
    s.text(214, 36, "seed_modules", "t-m")
    s.line(510, 48, 422, 48)
    s.box(260, 112, 160, 50, "kinds.py", L(lang, "checks keys + links", "kiểm key + liên kết"))
    s.line(340, 76, 340, 110)
    s.band(10, 184, 320, 166, L(lang, "WEB · /m/[module]", "WEB · /m/[module]"))
    s.box(26, 212, 288, 40, "WORKFLOW_BY_KIND[kind]", None, "n-box", "t")
    s.box(26, 262, 138, 72, "workflow", L(lang, "state + GraphQL", "state + GraphQL"))
    s.box(176, 262, 138, 72, "atoms", L(lang, "pure, props only", "thuần, chỉ props"))
    s.line(164, 298, 174, 298)
    s.band(350, 184, 320, 166, L(lang, "API · engines by kind", "API · engine theo kind"))
    s.box(366, 212, 140, 58, "tui_chat · 20", "tmux + claude TUI")
    s.box(516, 212, 140, 58, "oneshot · 19", "claude -p / codex")
    s.box(366, 280, 290, 54, L(lang, "13 bespoke kinds · 1 module each", "13 kind riêng · mỗi kind 1 module"),
          L(lang, "boards, learning, reasoning, decisions …", "bảng, học tập, suy luận, quyết định …"))
    s.path("M300 162 L170 182 L170 210", arrow=True)
    s.path("M380 162 L510 182 L510 210", arrow=True)
    return s


# 6 — UzAI site router: the end-to-end safe flow ----------------------------------------------------
def site(lang):
    s = Svg("pt-site", 900, 748,
            L(lang, "Real values live only in the browser; the server and the model see tokens and module ids",
              "Giá trị thật chỉ nằm trong trình duyệt; server và model chỉ thấy token và id module"),
            L(lang, "Three lanes: browser, server, model. Seven steps from a typed question to a prefilled module form, a variant for a missing value, and the guards.",
              "Ba làn: trình duyệt, server, model. Bảy bước từ câu hỏi đến form module đã điền sẵn, một biến thể khi thiếu giá trị, và các chốt chặn."))

    def rich(x, y, segs, base="t-m"):
        spans = "".join(f'<tspan class="{c}">{esc(t)}</tspan>' if c else esc(t) for t, c in segs)
        s.add(f'<text class="{base}" x="{x}" y="{y}" dominant-baseline="central">{spans}</text>')

    def card(x, y, h, title, lines, dashed=False):
        dash = ' stroke-dasharray="5 4"' if dashed else ""
        s.add(f'<rect class="n-box" x="{x}" y="{y}" width="264" height="{h}" rx="8"{dash}/>')
        s.add(f'<text class="t t-b" x="{x + 12}" y="{y + 20}" dominant-baseline="central">{esc(title)}</text>')
        for i, (base, segs) in enumerate(lines):
            rich(x + 12, y + 44 + i * 18, segs, base)

    swatches = [("n-bad", L(lang, "real value", "giá trị thật")), ("n-ok", L(lang, "token (masked)", "token (đã che)")),
                ("n-warn", L(lang, "left for the user to type", "để người dùng tự gõ"))]
    x = 12
    for cls, label in swatches:
        s.add(f'<rect class="{cls}" x="{x}" y="12" width="12" height="12" rx="3"/>')
        s.text(x + 18, 18, label, "t-s", "start")
        x += 34 + len(label) * 6.2

    lanes = [(12, L(lang, "BROWSER", "TRÌNH DUYỆT"), L(lang, "The only place real values live.", "Nơi duy nhất có giá trị thật.")),
             (306, L(lang, "SERVER · api", "SERVER · api"), L(lang, "Tokens and module ids. Checks everything.", "Token và id module. Kiểm mọi thứ.")),
             (600, L(lang, "MODEL · claude -p", "MODEL · claude -p"), L(lang, "Tokens and the module catalog only.", "Chỉ token và danh mục module."))]
    for lx, head, sub in lanes:
        s.band(lx, 40, 288, 552)
        s.text(lx + 12, 60, head, "t-h", "start")
        s.text(lx + 12, 78, sub, "t-s", "start")
    bx = [24, 318, 612]
    q = "đau đầu, sốt nhẹ từ "

    card(bx[0], 96, 84, L(lang, "1 Type the question", "1 Gõ câu hỏi"), [
        ("t-m", [(q, ""), ("12/10/2026", "t-bad")]),
        ("t-s", [(L(lang, "“headache, mild fever since …”", "ngày khớp luật che DATE trong DB"), "")]),
    ])
    card(bx[0], 200, 112, L(lang, "2 Masked in the browser", "2 Che ngay trong trình duyệt"), [
        ("t-m", [(q, ""), ("<DATE_1>", "t-ok")]),
        ("t-s", [(L(lang, "token map in sessionStorage (this tab):", "bảng token trong sessionStorage (tab này):"), "")]),
        ("t-m", [("<DATE_1>", "t-ok"), (" = ", ""), ("12/10/2026", "t-bad")]),
    ])
    card(bx[1], 200, 112, L(lang, "3 Server re-checks", "3 Server kiểm lại"), [
        ("t-m", [("sendSiteAssistantMessage", "")]),
        ("t-s", [(L(lang, "same mask rules again: tokens only", "chạy lại cùng luật che: chỉ còn token"), "")]),
        ("t-s", [(L(lang, "raw value: refused before any write", "còn giá trị thô: từ chối trước khi ghi"), "")]),
        ("t-s", [(L(lang, "and before the model is called", "và trước khi gọi model"), "")]),
    ])
    card(bx[2], 200, 112, L(lang, "4 What the model receives", "4 Model nhận được gì"), [
        ("t-m", [("… từ ", ""), ("<DATE_1>", "t-ok")]),
        ("t-m", [(L(lang, "dongy_triage | prefill:", "dongy_triage | điền sẵn:"), "")]),
        ("t-m", [("  symptom, started_when", "")]),
        ("t-s t-b", [(L(lang, "No path, no real value", "Không đường dẫn, không giá trị thật"), "")]),
    ])
    card(bx[2], 334, 112, L(lang, "5 The model picks a module", "5 Model chọn module"), [
        ("t-m", [("module: dongy_triage", "")]),
        ("t-m", [("symptom: đau đầu, sốt nhẹ", "")]),
        ("t-m", [("started_when: ", ""), ("<DATE_1>", "t-ok")]),
        ("t-s", [(L(lang, "it can name a value only by its token", "chỉ gọi được giá trị bằng token"), "")]),
    ])
    card(bx[1], 334, 112, L(lang, "6 Validate, then build the link", "6 Kiểm rồi mới dựng link"), [
        ("t-s", [(L(lang, "module in catalog · field exists", "module có trong danh mục · field có thật"), "")]),
        ("t-s", [(L(lang, "value is a substring of the question", "giá trị là chuỗi con của câu hỏi"), "")]),
        ("t-m", [("/m/dongy_triage?f.symptom=…", "")]),
        ("t-m", [("&f.started_when=", ""), ("<DATE_1>", "t-ok")]),
    ])
    card(bx[0], 334, 112, L(lang, "7 Unmask and open", "7 Bỏ che rồi mở"), [
        ("t-m", [("…started_when=", ""), ("12%2F10%2F2026", "t-bad")]),
        ("t-s", [(L(lang, "the triage form opens prefilled", "form “Quyết định đi khám” mở, đã điền"), "")]),
        ("t-s", [(L(lang, "the user still presses Run", "người dùng vẫn tự bấm Run"), "")]),
        ("t-s", [(L(lang, "value not in this tab: no Open button", "tab không có giá trị: không có nút Mở"), "")]),
    ])

    s.text(24, 470, L(lang, "Variant: the question lacks a value", "Biến thể: câu hỏi thiếu giá trị"), "t-h", "start")
    card(bx[2], 486, 92, L(lang, "The model leaves it out", "Model để trống field"), [
        ("t-m", [(L(lang, "prefill: symptom only", "prefill: chỉ symptom"), "")]),
        ("t-s", [(L(lang, "told never to invent a value", "được dặn không bao giờ bịa giá trị"), "")]),
        ("t-s", [(L(lang, "an invented one is dropped at step 6", "giá trị bịa vẫn bị bỏ ở bước 6"), "")]),
    ], dashed=True)
    card(bx[1], 486, 92, L(lang, "No placeholder in the link", "Link không có ô giữ chỗ"), [
        ("t-m", [("/m/dongy_triage?f.symptom=…", "")]),
        ("t-s", [(L(lang, "unlike Moza's {input:…} field", "khác ô {input:…} của Moza"), "")]),
        ("t-s", [(L(lang, "the module's own form asks instead", "form của module sẽ hỏi thay"), "")]),
    ], dashed=True)
    card(bx[0], 486, 92, L(lang, "The user types it in the form", "Người dùng gõ trong form"), [
        ("t-m", [("started_when [ ", ""), ("__________", "t-warn"), (" ]", "")]),
        ("t-s", [(L(lang, "the module's form is the input field", "form của module chính là ô nhập"), "")]),
        ("t-s", [(L(lang, "never asked inside the chat popup", "không hỏi trong popup chat"), "")]),
    ], dashed=True)

    s.line(156, 180, 156, 198)
    s.line(288, 256, 316, 256)
    s.line(582, 256, 610, 256)
    s.line(744, 312, 744, 332)
    s.line(612, 390, 584, 390)
    s.line(318, 390, 290, 390)
    s.line(612, 532, 584, 532)
    s.line(318, 532, 290, 532)

    s.add('<rect class="n-box" x="12" y="608" width="876" height="128" rx="10"/>')
    s.text(28, 630, L(lang, "Guards · each covered by a test", "Chốt chặn · mỗi cái có test"), "t-h", "start")
    guards = [
        L(lang, "Raw value in the question: refused before any write or model call", "Còn giá trị thô: từ chối trước khi ghi hay gọi model"),
        L(lang, "Module outside the catalog or unknown field: the link is dropped", "Module ngoài danh mục hoặc field lạ: bỏ cả link"),
        L(lang, "Prefill not found in the masked question: that value is dropped", "Giá trị không có trong câu hỏi đã che: bỏ giá trị đó"),
        L(lang, "URLs in the reply text are stripped; replies render as plain text", "URL trong lời đáp bị xóa; lời đáp hiện dạng chữ thường"),
        L(lang, "Stored mask rules that no longer parse: the router turns off", "Luật che trong DB không còn parse được: router tự tắt"),
        L(lang, "At most 3 links; an over-long path sheds prefills until it fits", "Tối đa 3 link; path quá dài thì bớt giá trị điền sẵn"),
    ]
    for i, g in enumerate(guards):
        gx, gy = 28 + (i // 3) * 436, 656 + (i % 3) * 24
        rich(gx, gy, [("✓ ", "t-ok"), (g, "")], "t-s")
    return s


def legend(s, items, y=18):
    x = 12
    for cls, label in items:
        s.add(f'<rect class="{cls}" x="{x}" y="{y - 6}" width="12" height="12" rx="3"/>')
        s.text(x + 18, y, label, "t-s", "start")
        x += 34 + len(label) * 6.2


def card(s, x, y, w, h, title, lines, cls="n-box"):
    s.add(f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/>')
    s.text(x + 12, y + 18, title, "t t-b", "start")
    for i, (base, text) in enumerate(lines):
        s.text(x + 12, y + 38 + i * 18, text, base, "start")


# 7 — Data model: the core and the domains that extend it ----------------------------------------
def schema(lang):
    s = Svg("pt-schema", 900, 568,
            L(lang, "A small core, and domains that hang off Module", "Một lõi nhỏ, các miền treo vào Module"),
            L(lang, "Core: catalog, session, profile. Every domain table has an FK to Module; arrows show the few links between domains.",
              "Lõi: catalog, session, profile. Mọi bảng miền có FK tới Module; mũi tên chỉ vài liên kết giữa các miền."))
    legend(s, [("n-new", L(lang, "core", "lõi")), ("n-box", L(lang, "engine domain", "miền engine")),
               ("n-info", L(lang, "shared by several domains", "dùng chung nhiều miền"))])
    s.band(12, 34, 876, 146, L(lang, "CORE · every table below has an FK to Module", "LÕI · mọi bảng bên dưới có FK tới Module"))
    card(s, 24, 66, 160, 100, "profile · 1", [("t-m", "Profile"), ("t-s", L(lang, "birth data for", "ngày sinh cho")),
                                             ("t-s", L(lang, "the metaphysics modules", "các module huyền học"))], "n-new")
    card(s, 196, 66, 332, 100, "session · 7", [
        ("t-m", "Session, Message, Report, Note,"), ("t-m", "LearningPoint, TurnLatency, PeriodSummary"),
        ("t-s", L(lang, "one run of any module; the lineage hub", "một lượt chạy của mọi module; trục lineage"))], "n-new")
    card(s, 540, 66, 336, 100, "catalog · 5", [
        ("t-m", "Module, Category, Tag, Voice,"), ("t-m", "ResearchTopic"),
        ("t-s", L(lang, "Module = kind + workflow_config: the hub", "Module = kind + workflow_config: trục chính"))], "n-new")
    s.line(196, 116, 186, 116)
    s.line(528, 116, 538, 116)

    cols = [24 + i * 172 for i in range(5)]
    bands = [
        (196, L(lang, "LINKED TO A RUN · via Session, Profile", "GẮN VỚI LƯỢT CHẠY · qua Session, Profile"), [
            ("forecast · 2", "ForecastRun, Outcome", "→ Profile", "n-box"),
            ("planner · 4", "Goal, PlanItem, …", "→ Session, Topic, Tag", "n-box"),
            ("must_win_goal · 2", "MustWinGoal, …Log", "→ Session, FocusGoal", "n-box"),
            ("focus · 3", "FocusGoal, …Task", L(lang, "→ Module only", "→ chỉ Module"), "n-box")]),
        (320, L(lang, "ENGINE DOMAINS · own tables, keyed to Module", "MIỀN ENGINE · bảng riêng, gắn với Module"), [
            ("learning_os · 15", "Concept, Hypothesis…", "→ Point ×3", "n-box"),
            ("event_reasoning · 11", "Event, Run, Law, …", "→ Point, ChangeItem", "n-box"),
            ("training · 5", "Case, Drill, Mastery", "→ Tag", "n-box"),
            ("decision · 5", "Decision, Layer, …", "→ Tag", "n-box"),
            ("paragraph · 2", "Paragraph, Sentence", L(lang, "→ Module only", "→ chỉ Module"), "n-box")]),
        (444, L(lang, "LEARNING SOURCES AND ASSISTANTS", "NGUỒN HỌC VÀ TRỢ LÝ"), [
            ("knowledge · 4", "Resource, Point, …", L(lang, "fed by the sync loop", "nạp bởi vòng sync"), "n-info"),
            ("agent · 4", "AiAgentProfile, …", L(lang, "lesson + site config", "cấu hình học + site"), "n-info"),
            ("ebook · 4", "Book, Chapter, …", "→ SourceDocument…", "n-box"),
            ("canonical · 13", "Source*, Lesson, …", "→ Module ×3", "n-info"),
            ("assistant · 3", "Thread, Message, …", "→ ConceptLesson", "n-box")]),
    ]
    for by, label, boxes in bands:
        s.band(12, by, 876, 112)
        s.text(876, by + 18, label, "t-h", "end")
        for i, (t, l1, l2, cls) in enumerate(boxes):
            card(s, cols[i], by + 30, 160, 72, t, [("t-m", l1), ("t-m", l2)], cls)
    s.line(104, 226, 104, 168)
    s.line(276, 226, 276, 168)
    s.line(448, 226, 448, 168)
    s.line(528, 262, 538, 262)
    s.line(196, 386, 186, 386)
    s.line(104, 422, 104, 472)
    s.path("M226 422 L176 472")
    s.line(528, 510, 538, 510)
    s.line(712, 510, 702, 510)
    return s


# 8 — Admin: where each setting starts, where it is edited, who reads it ---------------------------
def admin(lang):
    s = Svg("pt-admin", 900, 600,
            L(lang, "Admin settings: seeded from files, edited in one place, read by the runtime",
              "Admin: seed từ file, sửa ở một chỗ, runtime đọc lại"),
            L(lang, "Seven settings tabs, each between a source and the code that reads it, plus the two operating pages.",
              "Bảy tab cài đặt, mỗi tab nằm giữa nguồn và phần code đọc nó, cộng hai trang vận hành."))
    legend(s, [("n-new", L(lang, "writes the DB", "ghi vào DB")), ("n-box", L(lang, "read-only view", "chỉ xem")),
               ("n-info", L(lang, "acts on the host through the bridge", "tác động lên host qua bridge"))])
    heads = [(24, L(lang, "WHERE IT STARTS", "NGUỒN BAN ĐẦU")), (300, L(lang, "/admin/settings TAB", "TAB /admin/settings")),
             (636, L(lang, "WHO READS IT", "AI ĐỌC NÓ"))]
    for x, h in heads:
        s.text(x, 50, h, "t-h", "start")
    rows = [
        ("modules/*.yaml", L(lang, "seed_modules · insert-only", "seed_modules · chỉ insert"),
         "Modules", L(lang, "editor · kinds.py check · preview", "editor · kiểm kinds.py · xem trước"), "n-new",
         L(lang, "Module rows", "Dòng Module"), L(lang, "/m/[module], engines, Raycast, UzAI", "/m/[module], engine, Raycast, UzAI")),
        ("modules/_meta.yaml", L(lang, "category list", "danh sách nhóm"),
         "Categories", L(lang, "create · rename · reorder", "tạo · đổi tên · sắp xếp"), "n-new",
         L(lang, "Category rows", "Dòng Category"), L(lang, "catalog groups, UzAI catalogue", "nhóm danh mục, danh mục UzAI")),
        ("agents.yaml", L(lang, "seed_agents · insert-only", "seed_agents · chỉ insert"),
         "AI agent", L(lang, "1 profile · 2 per module · 3 whole site", "1 hồ sơ · 2 từng module · 3 toàn site"), "n-new",
         "UzAI", L(lang, "lesson assistant + site router", "trợ lý bài học + site router")),
        ("voices.yaml", L(lang, "seeded voices", "giọng seed sẵn"),
         "Voice", L(lang, "default voice · speak test", "giọng mặc định · nghe thử"), "n-new",
         L(lang, "Read aloud", "Đọc thành tiếng"), L(lang, "bridge say (macOS)", "bridge say (macOS)")),
        ("macOS keychain", L(lang, "a grant per CLAUDE_CONFIG_DIR", "grant theo CLAUDE_CONFIG_DIR"),
         "Credentials", L(lang, "status · sync · log in on the web", "trạng thái · đồng bộ · đăng nhập trên web"), "n-info",
         "bridge credential", L(lang, "login check before every spawn", "kiểm đăng nhập trước mỗi spawn")),
        ("bridge/settings.json", L(lang, "machine paths, CLI args", "đường dẫn máy, tham số CLI"),
         "Bridge", L(lang, "read-only · doctor + active sessions", "chỉ xem · doctor + số phiên sống"), "n-box",
         "phantinh-bridge", L(lang, "every host command", "mọi lệnh trên host")),
        (".env · compose", L(lang, "ports, URLs, limits", "cổng, URL, giới hạn"),
         "Infra", L(lang, "read-only · secrets redacted", "chỉ xem · che bí mật"), "n-box",
         L(lang, "api settings", "settings của api"), L(lang, "read once per process", "đọc một lần mỗi process")),
    ]
    for i, (lt, ls, mt, ms, mcls, rt, rs) in enumerate(rows):
        y = 64 + i * 60
        s.box(24, y, 230, 50, lt, ls)
        s.box(300, y, 290, 50, mt, ms, mcls)
        s.box(636, y, 240, 50, rt, rs)
        wire = "w-acc" if mcls == "n-new" else ("w" if mcls == "n-info" else "w-dash")
        s.line(254, y + 25, 298, y + 25, wire)
        s.line(590, y + 25, 634, y + 25, wire)
    s.band(12, 492, 876, 98, L(lang, "OPERATE · the two pages beside settings", "VẬN HÀNH · hai trang bên cạnh settings"))
    s.box(24, 524, 420, 54, "/admin/sessions",
          L(lang, "Session rows ↔ tmux: close, delete, reconcile, quality score",
            "Dòng Session ↔ tmux: đóng, xóa, đối chiếu, điểm chất lượng"))
    s.box(456, 524, 420, 54, "/admin/performance",
          L(lang, "TurnLatency: model / proxy / ingest / tool time per turn",
            "TurnLatency: thời gian model / proxy / ingest / tool mỗi lượt"))
    return s


# 9 — Troubleshooting from the admin pages ----------------------------------------------------------
def trouble(lang):
    s = Svg("pt-trouble", 900, 516,
            L(lang, "From a symptom to the admin page that explains it, and the fix",
              "Từ triệu chứng tới trang admin giải thích nó, và cách sửa"),
            L(lang, "Seven common symptoms; each row reads left to right: where to look, what you see, what fixes it.",
              "Bảy triệu chứng thường gặp; mỗi hàng đọc từ trái sang phải: xem ở đâu, thấy gì, sửa thế nào."))
    cols = [(24, 196, "n-warn"), (236, 180, "n-box"), (432, 220, "n-info"), (668, 208, "n-ok")]
    for (x, _, _), h in zip(cols, [L(lang, "SYMPTOM", "TRIỆU CHỨNG"), L(lang, "WHERE IN ADMIN", "XEM Ở ĐÂU"),
                                   L(lang, "WHAT YOU SEE", "THẤY GÌ"), L(lang, "FIX", "CÁCH SỬA")]):
        s.text(x, 40, h, "t-h", "start")
    rows = [
        [(L(lang, "Chat won't start", "Không mở được chat"), None),
         (L(lang, "Bridge tab", "Tab Bridge"), L(lang, "doctor: ok or degraded", "doctor: ok hay degraded")),
         ("SHIM_UNREACHABLE", L(lang, "or SHIM_REFUSED in the error", "hoặc SHIM_REFUSED trong lỗi")),
         (L(lang, "Start the host-shim", "Bật host-shim"), L(lang, "make dev; tokens must match", "make dev; token phải khớp"))],
        [(L(lang, "Spawn blocked by login", "Spawn bị chặn vì login"), None),
         (L(lang, "Credentials tab", "Tab Credentials"), L(lang, "a status dot per account", "chấm trạng thái mỗi tài khoản")),
         ("CLAUDE_LOGIN_EXPIRED", L(lang, "expired or not logged in", "hết hạn hoặc chưa đăng nhập")),
         (L(lang, "Sync the grant or log in", "Đồng bộ grant, đăng nhập"), L(lang, "from the same tab, on the web", "ngay trong tab, trên web"))],
        [(L(lang, "Sent, but no reply", "Gửi rồi, không hồi âm"), None),
         ("Sessions · quality", L(lang, "score green / amber / red", "điểm xanh / vàng / đỏ")),
         (L(lang, "stuck mid-stream, sync drift", "treo giữa stream, lệch sync"), L(lang, "JSONL has more turns than the DB", "JSONL nhiều lượt hơn DB")),
         ("reingest_session <sid>", L(lang, "CLI, outside admin; idempotent", "CLI, ngoài admin; idempotent"))],
        [(L(lang, "List and tmux disagree", "Danh sách lệch tmux"), None),
         ("Sessions · Reconcile", L(lang, "preview the diff first", "xem diff trước")),
         ("DB orphans · tmux orphans", L(lang, "a row without tmux, or the reverse", "dòng không tmux, hoặc ngược lại")),
         ("Apply fix", L(lang, "row → LOST, orphan tmux killed", "dòng → LOST, giết tmux mồ côi"))],
        [(L(lang, "One-shot never ends", "Oneshot chạy mãi"), None),
         ("Sessions · Running", L(lang, "the PROVISIONING filter", "bộ lọc PROVISIONING")),
         (L(lang, "running > 5 min, no lease", "chạy > 5 phút, mất lease"), L(lang, "or TIMEOUT after 600 s", "hoặc TIMEOUT sau 600 s")),
         (L(lang, "The reaper closes it", "Reaper tự đóng"), L(lang, "provisioning_timeout; run again", "provisioning_timeout; chạy lại"))],
        [(L(lang, "Answers are slow", "Trả lời chậm"), None),
         ("Performance", L(lang, "latency per turn, by stage", "độ trễ từng lượt theo chặng")),
         ("model / proxy / ingest / tool", L(lang, "TTFT > 30 s turns a session amber", "TTFT > 30 s → phiên màu vàng")),
         (L(lang, "Fix the slow stage", "Sửa chặng chậm"), L(lang, "proxy, tool use or the model", "proxy, tool hoặc chính model"))],
        [(L(lang, "Report missing/invalid", "Thiếu hoặc lỗi báo cáo"), None),
         ("Sessions · Modules", L(lang, "quality issues; ModuleEditor", "issue chất lượng; ModuleEditor")),
         (L(lang, "closed with no report", "đóng mà không có báo cáo"), L(lang, "or schema validation errors", "hoặc lỗi kiểm schema")),
         (L(lang, "Fix the schema or template", "Sửa schema hoặc template"), L(lang, "preview it in ModuleEditor", "xem trước trong ModuleEditor"))],
    ]
    for r, cells in enumerate(rows):
        y = 56 + r * 64
        for (x, w, cls), (t, sub) in zip(cols, cells):
            s.box(x, y, w, 52, t, sub, cls, "t t-b" if sub is None else "t t-b")
        for (x1, w1, _), (x2, _, _) in zip(cols, cols[1:]):
            s.line(x1 + w1, y + 26, x2 - 2, y + 26)
    return s


for fn in (layers, deploy, chat, states, dispatch, site, schema, admin, trouble):
    both(fn)
print("ok")
