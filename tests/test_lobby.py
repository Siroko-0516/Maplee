from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from maplee.content import AVATAR_JOBS


class LobbyElement:
    def __init__(self, text="", **attrs):
        self.attrs = attrs
        self.text = text
        self.value = ""
        self.hidden = self.disabled = False
        self.children = []
        self.events = {}
        self.focus = Mock()
        self.getContext = Mock(return_value=Mock())

    def bind(self, name, handler):
        self.events[name] = handler

    def clear(self):
        self.children.clear()

    def __le__(self, child):
        self.children.append(child)
        return self


class LobbyMarkup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.elements[attrs.pop("id")] = LobbyElement(**attrs)


class LobbyTests(unittest.TestCase):
    def setUp(self):
        markup = LobbyMarkup()
        markup.feed(Path(__file__).resolve().parents[1].joinpath("index.html").read_text())
        self.doc = markup.elements
        self.event = SimpleNamespace(preventDefault=Mock())
        self.request = Mock()
        self.app = SimpleNamespace(screen=SimpleNamespace(canvas=self.doc["interface"]),
                                   renderer=SimpleNamespace(ready=False), start_character=Mock())
        with patch.dict("sys.modules", {"browser": SimpleNamespace(document=self.doc,html=Mock(),window=Mock())}):
            from maplee import lobby
        html = SimpleNamespace(**dict.fromkeys(("BUTTON", "CANVAS", "DIV", "SMALL", "SPAN", "STRONG"), LobbyElement))
        bindings = patch.multiple(lobby,document=self.doc,html=html,api=self.request,local_read=Mock(return_value=None))
        bindings.start()
        self.addCleanup(bindings.stop)
        self.lobby = lobby.Lobby(self.app)
        self.idle_pose = lobby.idle_pose

    def test_signup_slots_job_and_name_then_enters_the_game(self):
        self.assertEqual(self.request.call_args.args[:3], ("GET", "/api/session", None))
        self.lobby.signed_in(401,{})
        self.doc["auth-mode"].events["click"](self.event)
        self.doc["lobby-id"].value = "forest_player"
        self.doc["lobby-password"].value = "valid-for-test"
        self.doc["lobby-credentials"].events["submit"](self.event)
        method,path,payload,finish = self.request.call_args.args
        self.assertEqual((method,path,payload["login"]),("POST","/api/signup","forest_player"))
        finish(200,{"account":"forest_player","slots":[None]*4})

        self.assertEqual(self.doc["lobby"].attrs["data-page"],"select")
        self.assertEqual(len(self.doc["lobby-slots"].children),4)
        self.doc["lobby-slots"].children[2].events["click"](self.event)
        self.doc["lobby-enter"].events["click"](self.event)
        self.assertEqual(self.doc["lobby"].attrs["data-page"],"jobs")
        self.assertEqual(len(self.doc["lobby-jobs"].children),len(AVATAR_JOBS))
        ranger = self.lobby.job_cards["ranger"][0]
        ranger.events["click"](self.event)
        self.assertEqual(ranger.attrs["aria-pressed"],"true")
        self.doc["lobby-job-next"].events["click"](self.event)

        self.assertEqual(self.doc["lobby"].attrs["data-page"],"create")
        self.assertIsNotNone(self.lobby.preview_pending)
        self.doc["character-name"].value = "숲길 궁수"
        self.doc["lobby-back-jobs"].events["click"](self.event)
        self.assertEqual(self.lobby.job,"ranger")
        self.doc["lobby-job-next"].events["click"](self.event)
        self.assertEqual(self.doc["character-name"].value,"숲길 궁수")
        self.doc["lobby-character"].events["submit"](self.event)
        method,path,body,finish = self.request.call_args.args
        self.assertEqual((method,path),("POST","/api/slot/2"))
        self.assertEqual((body["profile"]["name"],body["profile"]["job"]),("숲길 궁수","ranger"))
        state = {"level":1,"job":"ranger"}
        finish(201,{"profile":body["profile"],"revision":0,"progress":state})
        self.app.start_character.assert_called_once_with(body["profile"],state)
        self.assertTrue(self.doc["lobby"].hidden)

    def test_occupied_slot_goes_directly_to_its_saved_game(self):
        profile = dict(name="밤의 검사",job="guardian")
        self.lobby.signed_in(200,{"account":"old","slots":[None,{"profile":profile,"level":12},None,None]})
        self.assertEqual(self.lobby.selected_slot,1)
        self.assertEqual(self.doc["lobby-enter"].text,"플레이")
        self.doc["lobby-enter"].events["click"](self.event)
        method,path,body,finish = self.request.call_args.args
        self.assertEqual((method,path,body),("GET","/api/slot/1",None))
        state = dict(level=12, job="guardian", gold=777)
        finish(200,{"profile":profile,"revision":6,"progress":state})
        self.app.start_character.assert_called_once_with(profile,state)
        self.assertEqual(self.lobby.revision,6)

    def test_slot_silhouettes_and_featured_preview_draw_when_assets_are_ready(self):
        self.app.renderer.avatar = Mock()
        self.lobby.signed_in(200,{"account":"old","slots":[None]*4})
        self.app.renderer.ready = True
        self.lobby.flush_preview(0)
        empty = self.doc["lobby-slots"].children[0].children[1].children[0]
        empty.getContext.return_value.fillRect.assert_called_once_with(0,0,144,144)

        self.lobby.enter_selected(self.event)
        self.assertIs(self.lobby.featured[0],self.doc["lobby-job-preview"])
        previous = self.lobby.featured[1]
        tick = next(t for t in range(1,180) if self.idle_pose(t)!=previous)
        self.app.renderer.avatar.reset_mock()
        self.lobby.flush_preview((tick+.5)*1000/60)
        self.app.renderer.avatar.assert_called_once()
        self.assertEqual(self.lobby.featured[1],self.idle_pose(tick))
