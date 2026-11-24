import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from maplee.engine import Game


class MobileInterfaceTests(unittest.TestCase):
    def interface(self, width, height):
        browser = SimpleNamespace(
            window=SimpleNamespace(devicePixelRatio=2, matchMedia=lambda _: SimpleNamespace(matches=True), bind=Mock()),
            document={},
        )
        with patch.dict("sys.modules", {"browser": browser}):
            from maplee.windows import GameInterface
        canvas = Mock(attrs={}, style=SimpleNamespace())
        canvas.getBoundingClientRect.return_value = SimpleNamespace(left=0, top=0, width=width, height=height)
        app = SimpleNamespace(game=Game(), pointers={}, paused=False, panel=None,
                              action=Mock(), show_panel=Mock(), close_panel=Mock(), use_potion=Mock())
        with patch("maplee.windows.window", browser.window):
            screen = GameInterface(app, canvas, {"account":"계정"})
        for method in ("box", "bezel", "classic", "text", "icon"):
            setattr(screen, method, Mock())
        screen.ctx.measureText.return_value.width = 52
        return screen

    def event(self, screen, x, y, pointer=1):
        width = screen.canvas.getBoundingClientRect().width
        height = screen.canvas.getBoundingClientRect().height
        return SimpleNamespace(button=0, pointerId=pointer, clientX=x*width/screen.w,
                               clientY=y*height/screen.h, preventDefault=Mock())

    def test_thumb_controls_fit_portrait_and_short_landscape(self):
        for width,height in ((280,620), (320,568), (390,844), (720,330), (667,180)):
            with self.subTest(size=(width,height)):
                screen = self.interface(width,height)
                bottom = screen.dock()
                screen.touch(bottom)
                controls = [hit for hit in screen.hits if hit[6] == "hold"]
                self.assertEqual({hit[4] for hit in controls},
                                 {"ArrowLeft","ArrowRight","ArrowUp","ArrowDown","Space","KeyZ","KeyX","KeyV"})
                for i,(x,y,w,h,*_) in enumerate(controls):
                    self.assertGreaterEqual(w * width / screen.w, 43.5)
                    self.assertGreaterEqual(h * height / screen.h, 43.5)
                    self.assertTrue(0 <= x < x+w <= screen.w and 0 <= y < y+h <= bottom)
                    for a,b,c,d,*_ in controls[:i]:
                        self.assertFalse(a < x+w and x < a+c and b < y+h and y < b+d)
                self.assertTrue({"메뉴","HP 물약","MP 물약"} <= {hit[4] for hit in screen.hits})
                if height == 180:
                    self.assertEqual(len({hit[1] for hit in controls}),1)

    def test_two_fingers_and_direction_slide_release_cleanly(self):
        screen = self.interface(390,844)
        screen.touch(screen.dock())
        points = {hit[4]:(hit[0]+hit[2]/2,hit[1]+hit[3]/2) for hit in screen.hits if hit[6]=="hold"}
        left = self.event(screen,*points["ArrowLeft"])
        down = self.event(screen,*points["ArrowDown"])
        jump = self.event(screen,*points["Space"],pointer=2)
        screen.down(left)
        screen.down(jump)
        self.assertEqual(screen.app.pointers,{1:"ArrowLeft",2:"Space"})
        screen.move(down)
        self.assertEqual(screen.app.pointers,{1:"ArrowDown",2:"Space"})
        screen.up(jump)
        screen.cancel(down)
        self.assertEqual(screen.app.pointers,{})
        self.assertIn(("Space",),[entry.args for entry in screen.app.action.call_args_list])

    def test_panel_close_is_large_and_scroll_does_not_activate_rows(self):
        screen = self.interface(390,844)
        screen.app.panel = ("account",None)
        action = Mock()
        screen.app.rows = [("row","공용 월드","", "접속",action,False,None)]*12
        screen.panel_view(screen.dock())
        close = next(hit for hit in screen.hits if hit[4]=="닫기")
        self.assertGreaterEqual(close[2]*390/screen.w,43.5)
        self.assertGreaterEqual(close[3]*844/screen.h,43.5)
        button = next(hit for hit in screen.hits if hit[4]=="공용 월드 접속")
        x,y = button[0]+button[2]/2,button[1]+button[3]/2
        screen.down(self.event(screen,x,y))
        screen.move(self.event(screen,x,y-screen.tap_slop-6))
        self.assertGreater(screen.scroll,0)
        screen.move(self.event(screen,x,y))
        screen.up(self.event(screen,x,y))
        action.assert_not_called()
