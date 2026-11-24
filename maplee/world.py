"""Shared-world connection and short interpolation of remote players."""
from browser import window

from .content import WORLD_LAYOUT
from .engine import area_at, limit
from .lobby import FIELD_PROTOCOL, api
from .render import number


class SharedWorld:
    def __init__(self, app):
        self.app = app
        self.enabled = False
        self.mode = "shared"
        self.generation = 0
        self.actor = None
        self.inflight = False
        self.retry_at = 0
        self.server_time = self.received_at = self.last_success = self.last_sent = 0.0
        self.status = "접속 대기 중"
        self.players = {}
        self.sequence = 1
        self.batch = None
        self.operations = []
        self.move = None
        self.after_sync = None
        self.state_version = -1

    def start(self, mode="shared"):
        self.enabled = True
        self.mode = mode
        self.retry_at = 0
        self.set_status("공용 월드에 접속 중" if mode == "shared" else "혼자 하기 연결 중")

    def leave(self):
        self.release()
        self.generation += 1
        self.enabled = self.inflight = False
        self.actor = self.batch = self.move = self.after_sync = None
        self.players.clear()
        self.operations.clear()
        self.sequence = 1
        self.state_version = -1
        self.app.game.leave_shared_world()
        self.set_status("접속 대기 중")

    def release(self):
        if self.actor:
            api("POST","/api/world/leave",{"actor":self.actor},lambda *_:None,True)

    def set_status(self, value):
        if self.status != value:
            self.status = value
            if self.app.active and self.app.panel and self.app.panel[0] == "account":
                self.app.render_panel()

    def flush(self, callback):
        if self.actor and (self.operations or self.move is not None or self.batch):
            self.after_sync = callback
        else:
            callback()

    def wake(self):
        now = number(window.performance.now())
        self.retry_at = min(self.retry_at, max(self.last_sent + 125, now))

    def queue(self, action, argument, close=False):
        if not self.actor or len(self.operations) >= 36:
            self.app.toast("월드 연결을 확인하고 다시 시도해주세요.")
            return False
        self.operations.append(([action,argument],close))
        self.wake()
        return True

    def combat(self, action, argument):
        if not self.actor or len(self.operations) >= 36 or number(window.performance.now()) - self.last_success > 2200:
            return False
        game = self.app.game
        player = game.p
        self.operations.append(([action,argument,round(game.shared_clock),round(player["x"]),round(player["y"]),
                                 game.swing["dir"] if action == "attack" and game.swing else game.facing],False))
        self.wake()
        return True

    def travel(self, target):
        if self.actor and self.move is None and not (self.batch and self.batch[0].get("move") is not None):
            self.move = target
            self.wake()

    def pose(self):
        game = self.app.game
        player = game.p
        frame, facing = self.app.renderer.player_pose(game)
        swing = game.swing
        return dict(x=round(player["x"]),y=round(player["y"]),frame=frame,facing=facing,
                    swing=game.tick-swing["start"] if swing and swing["melee"] else None)

    def tick(self, now):
        if not self.enabled:
            return
        if self.actor:
            self.app.game.shared_clock = self.server_time + now - self.received_at
        if self.inflight or now < self.retry_at:
            return
        epoch = self.generation
        joining = self.actor is None
        if joining:
            payload = dict(protocol=FIELD_PROTOCOL,layout=WORLD_LAYOUT,pose=self.pose(),
                           slot=self.app.lobby.slot,mode=self.mode)
        else:
            if not self.batch:
                entries = self.operations[:24]
                del self.operations[:24]
                move = None if self.operations else self.move
                if not self.operations:
                    self.move = None
                payload = dict(protocol=FIELD_PROTOCOL,layout=WORLD_LAYOUT,pose=self.pose(),
                               seq=self.sequence,ops=[op for op, _ in entries],move=move,actor=self.actor,
                               stateVersion=self.state_version)
                self.batch = payload, entries
            payload = self.batch[0]
            if not payload["ops"] and payload["move"] is None:
                payload["pose"] = self.pose()
        self.inflight = True
        self.last_sent = now
        api("POST","/api/world/" + ("join" if joining else "sync"),payload,
            lambda status,data: self.receive(epoch,joining,now,status,data))

    def receive(self, epoch, joining, sent, status, data):
        if epoch != self.generation or not self.enabled:
            if joining and status == 200:
                api("POST","/api/world/leave",{"actor":data["actor"]},lambda *_:None,True)
            return
        self.inflight = False
        now = number(window.performance.now())
        if status != 200:
            self.retry_at = now + (160 if status == 429 else 300 if self.actor else 1600)
            if status == 410:
                mode = self.mode
                self.leave()
                self.start(mode)
            elif status in (401,409,426):
                self.leave()
                self.set_status(data.get("error","월드 연결이 끝났어요."))
                self.app.toast(self.status)
            elif status != 429:
                self.set_status("연결을 다시 시도하는 중")
            return
        interval = 125 if self.operations or self.move is not None else int(data["poll"])
        self.retry_at = max(sent+interval,now)
        self.last_success = now
        clock = float(data["now"]) + min(90, (now-sent)*.25)
        if not joining:
            estimate = self.server_time + now - self.received_at
            clock = estimate + limit((clock-estimate)*.3, -100, 100)
        self.server_time = clock
        self.received_at = now
        game = self.app.game
        game.shared_clock = self.server_time
        sample = data.get("sample")
        if joining:
            self.actor = data["actor"]
            game.enter_shared_world(self.combat)
            self.app.paused = False
            app_pose = data["pose"]
            if app_pose["x"] != round(game.p["x"]):
                game.travel(app_pose["x"])
        elif self.batch:
            payload, entries = self.batch
            self.batch = None
            self.sequence += 1
            if sample is None:
                sample = [payload["pose"][key] for key in ("x", "y")]
            for index, accepted in data.get("results",()):
                if accepted and entries[index][1]:
                    self.app.close_panel()
                elif not accepted:
                    self.app.toast("조건이 맞지 않거나 이미 처리된 동작이에요.")
            if payload.get("move") is not None and not data.get("warp"):
                self.app.toast("포털 가까이에서 다시 시도해주세요.")
        destination = data["pose"]
        warp = data.get("warp")
        if warp:
            self.app.arrive(destination["x"], warp)
        elif area_at(game.p["x"]) != data["region"]:
            game.travel(destination["x"])
        elif sample is not None:
            game.reconcile_field_pose(sample, destination)
        if data["stateVersion"] > self.state_version:
            self.state_version = data["stateVersion"]
            game.sync_progress(data["progress"], warp)
        for id, damage, effect in data.get("hits",()):
            monster = game.monsters[id]
            monster["hurt"] = game.tick + 10
            if not monster["spec"].get("elite"):
                monster["windup"] = 0
            game.show_hit(monster, damage, game.facing, effect)
        game.sync_shared_monsters(data["monsters"])
        self.set_players(data["players"],now)
        loot = data.get("loot")
        if loot:
            game.loot = (loot["gold"],loot["items"])
        self.set_status(f"{len(self.players)+1}명 접속 · 이 지역" if self.mode == "shared" else "혼자 플레이 중")
        if self.after_sync and not self.operations and self.move is None:
            callback, self.after_sync = self.after_sync, None
            callback()

    def set_players(self, players, now):
        previous = self.players
        self.players = {}
        for player in players:
            old = previous.get(player["id"])
            interval = limit(now-old["arrived"], 180, 650) if old else 320
            if old and abs(old["x"]-player["x"]) < 40+interval*.62 and abs(old["y"]-player["y"]) < 35+interval*1.6:
                x,y = self.interpolated(old,now)
            else:
                x,y = player["x"],player["y"]
            self.players[player["id"]] = dict(player,from_x=x,from_y=y,arrived=now,interval=interval)

    @staticmethod
    def interpolated(player, now):
        fraction = limit((now-player["arrived"])/player["interval"],0,1)
        return (player["from_x"]+(player["x"]-player["from_x"])*fraction,
                player["from_y"]+(player["y"]-player["from_y"])*fraction)

    def visible_players(self, now):
        if not self.actor or now-self.last_success > 2500:
            return ()
        region = area_at(self.app.game.p["x"])
        return [(player,*self.interpolated(player,now)) for player in self.players.values()
                if player["region"] == region]
