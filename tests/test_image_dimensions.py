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
    def test_backdrops_and_tiles_use_decoded_pixels(self):
        with patch.dict("sys.modules", {"browser": SimpleNamespace(window=None)}):
            from maplee.render import Renderer
        renderer = Renderer.__new__(Renderer)
        renderer.ctx = Mock()
        renderer.view_width,renderer.view_height = WIDTH,HEIGHT
        keys = {*(area["image"] for area in AREAS),
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
            self.assertEqual(len(calls),2)
            self.assertEqual(calls[0][5],0)
            self.assertEqual(calls[1][5],calls[0][3])
            self.assertEqual(calls[1][1],0)
            self.assertEqual(sum(call[3] for call in calls),WIDTH)
            for image,sx,sy,sw,sh,_,dy,dw,dh in calls:
                self.assertTrue(0 <= sx <= image.naturalWidth-sw)
                self.assertEqual(sy,64)
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
        renderer.scenery(Game(),AREAS[0],0,WIDTH,HEIGHT)
        stages = [call[0] for call in order.mock_calls]
        self.assertIn("terrain",stages)
        self.assertIn("ladder",stages)
        terrain_end = max(i for i,stage in enumerate(stages) if stage=="terrain")
        self.assertLess(terrain_end,stages.index("ladder"))
