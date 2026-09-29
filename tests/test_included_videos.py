import unittest
from scripts.generate_included_videos import TITLES, make_frames

class IncludedVideosTests(unittest.TestCase):
    def test_requested_catalog(self):
        self.assertEqual(TITLES, {'ingranaggi': 'Ingranaggi', 'tennis': 'Tennis',
                                  'pong': 'Pong', 'acquario': 'Acquario'})

    def test_four_distinct_seamless_grayscale_loops(self):
        signatures = set()
        for name in TITLES:
            frames = make_frames(name)
            self.assertEqual(len(frames), 30)
            self.assertTrue(all(f.size == (192, 108) and f.mode == 'L' for f in frames))
            self.assertEqual(len({f.tobytes() for f in frames}), 30)
            self.assertTrue(all(len(set(f.getdata())) <= 8 for f in frames))
            self.assertEqual(frames[0].tobytes(), make_frames(name, start=30)[0].tobytes())
            self.assertTrue(all(max(f.getdata()) > 150 for f in frames))
            signatures.add(frames[0].tobytes())
        self.assertEqual(len(signatures), 4)

if __name__ == '__main__': unittest.main()
