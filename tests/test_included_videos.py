import unittest
from scripts.generate_included_videos import TITLES, FPS, make_frames
from scripts.screensaver_art import ACTIONS

class IncludedVideosTests(unittest.TestCase):
    def test_requested_catalog(self):
        self.assertEqual(TITLES, {'naufrago': 'Isola deserta', 'orbita': 'Orbita',
                                  'acquario': 'Acquario', 'ingranaggi': 'Ingranaggi',
                                  'labirinto': 'Labirinto 3D'})

    def test_castaway_has_twelve_distinct_vignettes_and_quiet_boundaries(self):
        self.assertEqual(len(ACTIONS), 12)
        for style in ('color', 'bw'):
            episodes = [make_frames('naufrago', style=style, episode=i) for i in range(12)]
            self.assertEqual(len({frames[18 * FPS].tobytes() for frames in episodes}), 12)
            self.assertEqual(len({frames[0].tobytes() for frames in episodes}), 1)
            for frames in episodes:
                self.assertEqual(len(frames), 30 * FPS)
                self.assertNotEqual(frames[8 * FPS].tobytes(), frames[18 * FPS].tobytes())

    def test_five_distinct_seamless_loops_in_both_styles(self):
        signatures = set()
        for name in TITLES:
            for style, size, mode in [('bw', (192, 108), 'L'), ('color', (256, 144), 'RGB')]:
                frames = make_frames(name, style=style)
                self.assertEqual(len(frames), 30 * FPS)
                self.assertTrue(all(f.size == size and f.mode == mode for f in frames))
                self.assertEqual(len({f.tobytes() for f in frames}), 30 * FPS)
                self.assertEqual(frames[0].tobytes(), make_frames(name, start=30, style=style)[0].tobytes())
                if style == 'bw':
                    self.assertTrue(all(len(set(f.getdata())) <= 8 for f in frames))
                else:
                    self.assertTrue(any(r != g or g != b for r, g, b in frames[0].getdata()))
                signatures.add(frames[0].tobytes())
        self.assertEqual(len(signatures), 10)

if __name__ == '__main__': unittest.main()
