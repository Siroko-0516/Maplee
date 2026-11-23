"""Maplee account, character selection, and acknowledged autosaves."""
import json
from browser import document, html, window
from .content import AVATAR_JOBS, CLASSES, STARTER_WEAPONS, avatar_style
from .engine import SAVE_KEY


def api(method, path, data, callback, keepalive=False):
    payload = "" if data is None else json.dumps(data, ensure_ascii=False)
    window.mapleeRequest(method, path, payload, keepalive,
                         lambda status, raw: callback(int(status), json.loads(str(raw))))


def local_read(key):
    try:
        return json.loads(window.localStorage.getItem(key) or "null")
    except Exception:
        return None


class Lobby:
    def __init__(self, app):
        self.app = app
        self.account = None
        self.slots = []
        self.slot = None
        self.pending = None
        self.saving = False
        self.inflight = None
        self.blocked = False
        self.busy = False
        self.mode = "login"
        self.job = "beginner"
        self.profile = None
        self.message = "자동저장 대기 중"
        self.preview_pending = None
        self.after_save = None
        self.view("auth")
        document["lobby-credentials"].bind("submit", self.authenticate)
        document["auth-mode"].bind("click", self.auth_mode)
        document["lobby-character"].bind("submit", self.create)
        document["lobby-import"].bind("click", lambda _: self.create(legacy=True))
        document["lobby-back"].bind("click", lambda _: self.show_slots())
        document["lobby-signout"].bind("click", lambda _: self.logout())
        document["character-style"].bind("change", lambda _: self.update_style())
        for name in ("sex","skin","hair"):
            document["character-"+name].bind("change", lambda _: self.draw_jobs())
        document["auth-submit"].disabled = True
        api("GET","/api/session",None,self.signed_in)

    def status(self, message):
        document["lobby-status"].text = message

    def view(self, page):
        document["lobby"].hidden = False
        self.app.screen.canvas.attrs["tabindex"] = "-1"
        for item in ("auth","select","create"):
            document["lobby-"+item].hidden = item != page
        document["lobby-signout"].hidden = not self.account

    def auth_mode(self, _):
        self.mode = "signup" if self.mode == "login" else "login"
        signup = self.mode == "signup"
        document["auth-title"].text = "Maplee 회원가입" if signup else "Maplee 로그인"
        document["auth-submit"].text = "가입하고 시작" if signup else "로그인"
        document["auth-mode"].text = "로그인 화면" if signup else "회원가입"
        document["lobby-password"].attrs["autocomplete"] = "new-password" if signup else "current-password"
        self.status("")

    def authenticate(self, event):
        event.preventDefault()
        if self.busy or document["auth-submit"].disabled:
            return
        self.busy = True
        document["auth-submit"].disabled = True
        self.status("계정을 확인하는 중이에요.")
        api("POST","/api/"+self.mode,{"login":document["lobby-id"].value,
                                      "password":document["lobby-password"].value},self.signed_in)

    def signed_in(self, status, data):
        attempted = self.busy
        self.busy = False
        document["auth-submit"].disabled = False
        if status == 200:
            document["lobby-password"].value = ""
            self.account = data["account"]
            self.slots = data["slots"]
            self.show_slots()
        elif not attempted and status == 401 and self.account:
            self.account = None
            self.view("auth")
            self.status("세션이 끝났어요. 다시 로그인해주세요.")
        elif attempted or status != 401:
            self.status(data.get("error","계정 서버에 연결할 수 없어요."))

    def require_preview(self, action):
        if self.app.renderer.ready:
            action()
        else:
            self.preview_pending = action

    def flush_preview(self):
        if self.preview_pending and self.app.renderer.ready:
            action, self.preview_pending = self.preview_pending, None
            action()

    def portrait(self, canvas, profile, starter=False):
        ctx = canvas.getContext("2d")
        ctx.imageSmoothingEnabled = False
        size = int(canvas.attrs["width"])
        ctx.clearRect(0,0,size,size)
        job = profile["job"]
        weapon = STARTER_WEAPONS[job] if starter else None
        self.app.renderer.avatar(ctx,{},weapon,0,size*38/80,size*75/80,size,1,
                                 job=job,profile=profile,preview=True)

    def show_slots(self):
        self.preview_pending = None
        self.view("select")
        self.status(f"{self.account} · 캐릭터 {sum(item is not None for item in self.slots)}/4")
        holder = document["lobby-slots"]
        holder.clear()
        previews = []
        for index, entry in enumerate(self.slots):
            card = html.BUTTON(Class="lobby-card", type="button")
            card <= html.SMALL(f"슬롯 {index+1}")
            if entry:
                canvas = html.CANVAS(width=80,height=80)
                card <= canvas
                card <= html.STRONG(entry["profile"]["name"])
                card <= html.SMALL(f"Lv. {entry['level']} · {CLASSES[entry['profile']['job']]['name']}")
                card.bind("click", lambda _, index=index: self.select(index))
                previews.append((canvas,entry["profile"]))
            else:
                card <= html.STRONG("+ 캐릭터 만들기")
                card.bind("click", lambda _, index=index: self.open_creator(index))
            holder <= card
        self.require_preview(lambda: [self.portrait(canvas,p) for canvas,p in previews])

    def open_creator(self, slot):
        if self.busy:
            return
        self.slot = slot
        self.job = "beginner"
        document["character-name"].value = ""
        document["character-style"].value = "classic"
        for field in ("sex","skin","hair"):
            document["character-"+field].value = "0"
        document["lobby-import"].hidden = not bool(local_read(SAVE_KEY))
        self.view("create")
        self.status(f"슬롯 {slot+1}")
        self.update_style()

    def update_style(self):
        custom = document["character-style"].value == "custom"
        for field in ("sex","skin","hair"):
            document["appearance-"+field].hidden = not custom
        self.draw_jobs()

    def looks(self, job):
        return dict(job=job, style=document["character-style"].value, **{field:int(document["character-"+field].value)
                                for field in ("sex","skin","hair")})

    def draw_jobs(self):
        def draw():
            holder = document["lobby-jobs"]
            holder.clear()
            for job in AVATAR_JOBS:
                choices = self.looks(job)
                card = html.BUTTON(Class="lobby-card",type="button",
                                   **{"aria-pressed":"true" if job==self.job else "false"})
                canvas = html.CANVAS(width=80,height=80)
                card <= canvas
                card <= html.STRONG(CLASSES[job]["name"])
                card <= html.SMALL(CLASSES[job]["skill"])
                card.bind("click",lambda _, job=job: self.choose_job(job))
                holder <= card
                self.portrait(canvas,choices,starter=True)
            self.portrait(document["lobby-preview"],self.looks(self.job),starter=True)
        self.require_preview(draw)

    def choose_job(self, job):
        self.job = job
        self.draw_jobs()

    def create(self, event=None, legacy=False):
        if event:
            event.preventDefault()
        if self.busy:
            return
        profile = self.looks(self.job)
        previous = local_read(SAVE_KEY) if legacy else None
        profile["name"] = document["character-name"].value.strip() or ("기존 모험가" if legacy else "")
        self.load_slot("POST",self.slot,{"profile":profile,"legacy":previous},legacy and bool(previous))

    def select(self, slot):
        self.load_slot("GET",slot,None)

    def load_slot(self, method, slot, payload, imported=False):
        if self.busy:
            return
        self.busy = True
        document["character-submit"].disabled = True
        self.status("캐릭터를 불러오는 중이에요.")
        def loaded(status,data):
            self.busy = False
            document["character-submit"].disabled = False
            if status >= 400 or not status:
                self.status(data.get("error","캐릭터 서버에 연결할 수 없어요."))
                return
            self.slot = slot
            self.profile = data["profile"]
            self.revision = data["revision"]
            self.pending = None
            self.blocked = False
            self.after_save = None
            progress = data.get("progress")
            draft = local_read(self.draft_key())
            if draft and (draft.get("revision") == self.revision or
                          draft.get("revision") == self.revision-1 and
                          draft.get("inflight") == self.serialize(progress)):
                progress = draft.get("progress",progress)
            self.profile["style"] = avatar_style(self.profile,progress)
            self.acknowledged = self.serialize(data.get("progress"))
            self.message = "자동저장 대기 중"
            if imported:
                try:
                    window.localStorage.removeItem(SAVE_KEY)
                except Exception:
                    pass
            document["lobby"].hidden = True
            self.app.screen.canvas.attrs["tabindex"] = "0"
            self.app.start_character(self.profile,progress)
        api(method,f"/api/slot/{slot}",payload,loaded)

    def logout(self):
        if self.busy:
            return
        self.busy = True
        def complete(status,data):
            self.busy = False
            if status in (200,401):
                self.account = None
                self.slot = None
                self.view("auth")
                self.status("")
            else:
                self.status(data.get("error","로그아웃에 실패했어요."))
        api("POST","/api/logout",{},complete)

    def draft_key(self):
        return f"maplee-draft-v2:{self.account}:{self.slot}"

    @staticmethod
    def serialize(progress):
        return json.dumps(progress, ensure_ascii=False, sort_keys=True)

    def save_progress(self, progress, keepalive=False):
        if not self.profile:
            return False
        serialized = self.serialize(progress)
        if serialized == self.acknowledged and not self.saving:
            return True
        self.pending = serialized
        self.keep_draft(serialized)
        if not self.saving and not self.blocked:
            self.send_save(keepalive)
        return not self.blocked

    def keep_draft(self, serialized):
        try:
            window.localStorage.setItem(self.draft_key(),json.dumps(
                {"revision":self.revision,"progress":json.loads(serialized),"inflight":self.inflight},ensure_ascii=False))
        except Exception:
            pass

    def send_save(self, keepalive=False):
        sent, self.pending = self.pending, None
        self.saving = True
        self.inflight = sent
        self.message = "저장 중…"
        def complete(status,data):
            self.saving = False
            self.inflight = None
            if status == 200:
                self.revision = data["revision"]
                self.acknowledged = sent
                self.message = "자동저장 완료"
                if self.pending and self.pending != sent:
                    self.keep_draft(self.pending)
                    self.send_save(keepalive)
                    return
                self.pending = None
                try:
                    window.localStorage.removeItem(self.draft_key())
                except Exception:
                    pass
                if self.after_save:
                    callback, self.after_save = self.after_save, None
                    callback()
            else:
                self.pending = self.pending or sent
                self.blocked = status in (401,409)
                self.message = data.get("error","네트워크 연결을 확인한 뒤 다시 저장해주세요.")
                self.after_save = None
                if not keepalive:
                    self.app.toast(self.message)
            if self.app.active and self.app.panel and self.app.panel[0] == "account":
                self.app.render_panel()
        api("PUT",f"/api/slot/{self.slot}",{"progress":json.loads(sent),"revision":self.revision},
            complete,keepalive)

    def leave(self):
        if self.blocked:
            self.return_to_slots()
            return
        self.after_save = self.return_to_slots
        self.app.save()
        if not self.saving and not self.pending:
            self.after_save = None
            self.return_to_slots()

    def return_to_slots(self):
        self.profile = None
        self.app.leave_character()
        self.view("select")
        document["lobby-slots"].clear()
        self.status("캐릭터 목록을 불러오는 중이에요.")
        api("GET","/api/session",None,self.signed_in)
