import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from maplee.content import AREAS


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
        keys = {"background", *(area.get("image", "background") for area in AREAS),
                *(area["material"] for area in AREAS)}
        renderer.images = {key: IntrinsicImage() for key in keys}
        renderer.sizes, renderer.loaded, renderer.failed = {}, set(), set()
        for key, image in renderer.images.items():
            renderer.image_loaded(key, image)
        for area in AREAS:
            renderer.backdrop(area, area["start"])
            image, sx, _, sw, sh, *_ = renderer.ctx.drawImage.call_args.args
            self.assertTrue(0 <= sx <= image.naturalWidth-sw)
            self.assertTrue(0 < sh <= image.naturalHeight)
            renderer.tile_band(area["material"], area["start"], area["start"]+960, True)
