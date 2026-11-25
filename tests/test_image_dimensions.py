import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from maplee.content import AREAS
from maplee.engine import HEIGHT, WIDTH, Game


class IntrinsicImage:
    """Detached image with decoded pixels but no usable layout dimensions."""
    naturalWidth = 1536
    naturalHeight = 768

    @property
    def width(self):
        raise AssertionError("Renderer used CSS width for image arithmetic")

    @property
    def height(self):
        raise AssertionError("Renderer used CSS height for image arithmetic")


class ImageDimensionTest(unittest.TestCase):
    def test_walkable_seam_blends_the_two_panoramas(self):
        with patch.dict("sys.modules", {"browser": SimpleNamespace(window=None)}):
            from maplee.render import Renderer
        renderer = Renderer.__new__(Renderer)
        renderer.ctx, renderer.backdrop = Mock(), Mock()
        seam = AREAS[0]["end"]
        renderer.field_backdrop(1,seam,seam-480,0)
        self.assertEqual([call.args[0] for call in renderer.backdrop.call_args_list],[AREAS[0],AREAS[1]])
        self.assertEqual(renderer.ctx.globalAlpha,.5)
        renderer.backdrop.reset_mock()
        boundary = AREAS[2]["end"]
        renderer.field_backdrop(2,boundary-24,boundary-960,0)
        renderer.backdrop.assert_called_once_with(AREAS[2],boundary-960,0)

    def test_field_view_spans_more_world_at_the_same_screen_size(self):
        with patch.dict("sys.modules", {"browser": SimpleNamespace(window=None)}):
            from maplee.render import Renderer
        renderer = Renderer.__new__(Renderer)
        renderer.canvas = Mock(attrs={"height": "", "width": ""})
        renderer.canvas.getBoundingClientRect.return_value = SimpleNamespace(width=1280, height=720)
        with patch("maplee.render.window", SimpleNamespace(devicePixelRatio=1)):
            renderer.resize()
        self.assertEqual((renderer.view_width, renderer.view_height), (1040, 585))

    def test_backdrops_and_tiles_use_decoded_pixels(self):
        with patch.dict("sys.modules", {"browser": SimpleNamespace(window=None)}):
            from maplee.render import Renderer
        renderer = Renderer.__new__(Renderer)
        renderer.ctx = Mock()
        renderer.view_width,renderer.view_height = WIDTH,HEIGHT
        keys = {*(area["image"] for area in AREAS),
                *(area["mid_image"] for area in AREAS if "mid_image" in area),
                *(area["material"] for area in AREAS)}
        renderer.images = {key: IntrinsicImage() for key in keys}
        renderer.sizes, renderer.loaded, renderer.failed = {}, set(), set()
        for key, image in renderer.images.items():
            renderer.image_loaded(key, image)
        for area in AREAS:
            renderer.ctx.reset_mock()
            # Force the viewport across the edge of the repeating texture.
            renderer.backdrop({**area, "view":1500}, area["start"], -160)
            calls = [call.args for call in renderer.ctx.drawImage.call_args_list]
            self.assertEqual(len(calls), 4 if "mid_image" in area else 2)
            for i in range(0,len(calls),2):
                layer = calls[i:i+2]
                self.assertEqual(layer[0][5],0)
                self.assertEqual(layer[1][5],layer[0][3])
                self.assertEqual(layer[1][1],0)
                self.assertEqual(sum(call[3] for call in layer),WIDTH)
                for image,sx,sy,sw,sh,_,dy,dw,dh in layer:
                    self.assertTrue(0 <= sx <= image.naturalWidth-sw)
                    self.assertEqual(sy,64 if i==0 else 32)
                    self.assertTrue(0 <= sy <= image.naturalHeight-sh)
                    self.assertEqual((sw,sh,dy),(dw,dh,0))
                    self.assertEqual(dh,HEIGHT)
            renderer.tile_band(area["material"], area["start"], area["start"]+960, HEIGHT)

    def test_ladder_is_drawn_after_floating_terrain(self):
        with patch.dict("sys.modules", {"browser": SimpleNamespace(window=None)}):
            from maplee.render import Renderer
        renderer = Renderer.__new__(Renderer)
        renderer.ctx = Mock()
        renderer.images = {"props":IntrinsicImage()}
        renderer.ground = Mock()
        order = Mock()
        order.attach_mock(Mock(),"terrain")
        order.attach_mock(Mock(),"ladder")
        renderer.tile_band = order.terrain
        renderer.ladder = order.ladder
        renderer.sprite = Mock()
        renderer.label = Mock()
        renderer.rect = Mock()
        renderer.static_scenery(0,0,WIDTH,HEIGHT)
        stages = [call[0] for call in order.mock_calls]
        self.assertIn("terrain",stages)
        self.assertIn("ladder",stages)
        terrain_end = max(i for i,stage in enumerate(stages) if stage=="terrain")
        self.assertLess(terrain_end,stages.index("ladder"))

    def test_overlapping_viewports_reuse_terrain_and_bound_memory(self):
        with patch.dict("sys.modules", {"browser": SimpleNamespace(window=None)}):
            from maplee.render import Renderer, TERRAIN_CACHE_SIZE
        renderer = Renderer.__new__(Renderer)
        renderer.ctx = Mock()
        renderer.terrain_cache = {}
        renderer.static_scenery = Mock()
        document = SimpleNamespace(createElement=lambda _: Mock(attrs={}))
        with patch("maplee.render.window",SimpleNamespace(document=document)):
            renderer.terrain(0,0,WIDTH)
            renderer.terrain(0,30,WIDTH+30)
            self.assertEqual(renderer.static_scenery.call_count,2)
            self.assertEqual(renderer.ctx.drawImage.call_count,4)
            for region,area in enumerate(AREAS):
                renderer.terrain(region,area["start"],area["start"]+WIDTH)
        self.assertEqual(len(renderer.terrain_cache),TERRAIN_CACHE_SIZE)
