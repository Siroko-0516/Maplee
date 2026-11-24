"""Shared-world connection and short interpolation of remote players."""
from browser import window

from .content import WORLD_LAYOUT
from .engine import area_at, limit
from .lobby import api
from .render import number


class SharedWorld:
    def __init__(self, app):
        self.app = app
        self.enabled = False
        self.generation = 0
        self.actor = None
        self.inflight = False
        self.retry_at = 0
        self.server_time = 0.0
        self.received_at = 0.0
        self.last_success = 0.0
        self.status = "혼자 플레이 중"
        self.players = {}
        self.sequence = 1
        self.batch = None
        self.hits = []
        self.ack = set()
        self.rewarded = set()

    def start(self):
        self.enabled = True
        self.retry_at = 0
        self.set_status("공용 월드에 접속 중")

    def leave(self):
        self.release()
        self.generation += 1
        self.enabled = self.inflight = False
        self.actor = self.batch = None
        self.players.clear()
        self.hits.clear()
        self.ack.clear()
        self.rewarded.clear()
        self.sequence = 1
        self.app.game.leave_shared_world()
        self.set_status("혼자 플레이 중")

    def release(self):
        if self.actor:
            api("POST","/api/world/leave",{"actor":self.actor},lambda *_:None,True)

    def set_status(self, value):
        if self.status != value:
            self.status = value
            if self.app.active and self.app.panel and self.app.panel[0] == "account":
                self.app.render_panel()

    def queue_hit(self, monster, power):
        if len(self.hits) >= 90 or number(window.performance.now()) - self.last_success > 2600:
            return False
        player = self.app.game.p
        self.hits.append(dict(id=monster["id"],life=monster["life"],power=round(power),
                              x=round(player["x"]),y=round(player["y"])))
        return True

    def pose(self):
        game = self.app.game
        player = game.p
        frame, facing = self.app.renderer.player_pose(game)
        swing = game.swing
        equipment = dict(player["equipment"])
        if swing:
            equipment["weapon"] = swing["weapon"]
        return dict(x=round(player["x"]),y=round(player["y"]),job=player["job"],level=player["level"],
                    equipment=equipment,frame=frame,facing=facing,
                    swing=game.tick-swing["start"] if swing and swing["melee"] else None)

    def tick(self, now):
        if not self.enabled:
            return
        if self.actor:
            self.app.game.shared_clock = self.server_time + now - self.received_at
        if self.inflight or now < self.retry_at:
            return
        if self.actor and not self.batch:
            self.batch = dict(seq=self.sequence, hits=self.hits[:30], ack=sorted(self.ack)[:60])
            del self.hits[:30]
            self.sequence += 1
        epoch = self.generation
        joining = self.actor is None
        args = dict(layout=WORLD_LAYOUT,pose=self.pose())
        if joining:
            args["slot"] = self.app.lobby.slot
        else:
            args.update(self.batch,actor=self.actor)
        self.inflight = True
        api("POST","/api/world/" + ("join" if joining else "sync"),args,
            lambda status, data: self.receive(epoch,joining,now,status,data))

    def receive(self, epoch, joining, sent, status, data):
        if epoch != self.generation or not self.enabled:
            if joining and status == 200:
                api("POST","/api/world/leave",{"actor":data["actor"]},lambda *_:None,True)
            return
        self.inflight = False
        now = number(window.performance.now())
        if status != 200:
            self.retry_at = now + (650 if self.actor else 2300)
            if status == 410:
                self.leave()
                self.start()
            elif status in (401,409,426):
                self.leave()
                self.set_status(data.get("error","월드 연결이 끝났어요."))
                self.app.toast(self.status)
            elif status != 429:
                self.set_status("연결을 다시 시도하는 중")
            return
        self.retry_at = max(sent+int(data["poll"]),now)
        self.last_success = now
        self.server_time = float(data["now"]) + (now-sent)*.5
        self.received_at = now
        game = self.app.game
        game.shared_clock = self.server_time
        if joining:
            self.actor = data["actor"]
            game.enter_shared_world(self.queue_hit)
            self.app.paused = False
        elif self.batch:
            self.ack.difference_update(self.batch["ack"])
            self.batch = None
        game.sync_shared_monsters(data["monsters"])
        self.set_players(data["players"],now)
        rewarded = False
        for event in data["rewards"]:
            key = event["event"]
            if key not in self.rewarded:
                game.grant_monster_reward(game.monsters[event["monster"]],event["x"])
                self.rewarded.add(key)
                rewarded = True
            self.ack.add(key)
        if rewarded:
            game.dirty = True
            self.app.save()
        self.set_status(f"{len(self.players)+1}명 접속 · 이 지역")

    def set_players(self, players, now):
        previous = self.players
        self.players = {}
        for player in players:
            old = previous.get(player["id"])
            if old and abs(old["x"]-player["x"]) < 230 and abs(old["y"]-player["y"]) < 165:
                x,y = self.interpolated(old,now)
            else:
                x,y = player["x"],player["y"]
            self.players[player["id"]] = dict(player,from_x=x,from_y=y,arrived=now)

    @staticmethod
    def interpolated(player, now):
        fraction = limit((now-player["arrived"])/230,0,1)
        return (player["from_x"]+(player["x"]-player["from_x"])*fraction,
                player["from_y"]+(player["y"]-player["from_y"])*fraction)

    def visible_players(self, now):
        if not self.actor or now-self.last_success > 2500:
            return ()
        region = area_at(self.app.game.p["x"])
        return [(player,*self.interpolated(player,now)) for player in self.players.values()
                if player["region"] == region]
