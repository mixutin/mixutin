"""Offline regression checks for the profile README and its banner."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / 'README.md').read_text(encoding='utf-8')
SVG = ROOT / 'assets/banner.svg'


class Markup(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.tags = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class ProfileTests(unittest.TestCase):
    def test_profile_alias(self):
        self.assertIn('mixutin / 0x11a', README)

    def test_featured_projects_and_credit(self):
        for name in ('Vibrix', 'Lumina', 'Mallow', 'dauntless-revived', 'JKI'):
            self.assertIn(f'https://github.com/mixutin/{name}', README)
        for text in ('https://github.com/SyST3MDeV/Undaunted', 'AGPL-3.0',
                     'does not run Windows programs yet', 'Pre-alpha', 'Experimental OS'):
            self.assertIn(text, README)

    def test_links_and_local_assets(self):
        markup = Markup(README)
        links = re.findall(r'\]\(([^\s)]+)\)', README)
        for _, attrs in markup.tags:
            links.extend(attrs[k] for k in ('href', 'src') if k in attrs)
        self.assertTrue(links)
        for link in links:
            parts = urlsplit(link)
            if parts.scheme or parts.netloc:
                self.assertEqual(parts.scheme, 'https', link)
                self.assertTrue(parts.hostname, link)
            else:
                target = (ROOT / parts.path).resolve()
                self.assertTrue(target.is_relative_to(ROOT), link)
                self.assertTrue(target.is_file(), link)
        images = [attrs for tag, attrs in markup.tags if tag == 'img']
        self.assertEqual(len(images), 1)
        self.assertTrue(images[0].get('alt', '').strip())
        self.assertEqual(images[0]['src'], 'assets/banner.svg')

    def test_readme_has_no_active_markup_or_remote_images(self):
        for tag, attrs in Markup(README).tags:
            self.assertNotIn(tag, {'script', 'iframe', 'style', 'object', 'embed'})
            self.assertFalse(any(key.lower().startswith('on') for key in attrs))
        self.assertNotIn('img.shields.io', README)
        self.assertNotIn('3D STUDY', README)

    def test_banner_is_self_contained_accessible_svg(self):
        text = SVG.read_text(encoding='utf-8')
        self.assertLess(SVG.stat().st_size, 20000)
        self.assertNotIn('<!DOCTYPE', text.upper())
        root = ET.fromstring(text)
        self.assertEqual(root.tag, '{http://www.w3.org/2000/svg}svg')
        self.assertEqual(root.attrib['viewBox'], '0 0 1200 400')
        ids = [node.attrib['id'] for node in root.iter() if 'id' in node.attrib]
        self.assertEqual(len(ids), len(set(ids)))
        for label in root.attrib['aria-labelledby'].split():
            self.assertIn(label, ids)
        for node in root.iter():
            self.assertNotIn(node.tag.split('}')[-1].lower(),
                             {'script', 'foreignobject', 'image', 'animate', 'set', 'style'})
            for attr, value in node.attrib.items():
                self.assertFalse(attr.lower().startswith('on'))
                if attr.split('}')[-1] == 'href':
                    self.assertTrue(value.startswith('#'))
                for target in re.findall(r'url\(#([^)]*)\)', value):
                    self.assertIn(target, ids)
        self.assertNotIn('3D STUDY', text)

    def test_finnish_section_and_repository_hygiene(self):
        self.assertEqual(README.count('<details>'), 1)
        self.assertEqual(README.count('</details>'), 1)
        self.assertIn('Suomeksi', README)
        self.assertIn('https://mixutin.github.io/fi/', README)
        self.assertIn('SECURITY.md', README)
        self.assertNotIn('In private development', README)
        for path in (ROOT / 'README.md', SVG):
            text = path.read_text(encoding='utf-8')
            self.assertTrue(text.endswith('\n'), path)
            self.assertFalse(any(line.endswith((' ', '\t')) for line in text.splitlines()), path)


if __name__ == '__main__':
    unittest.main()
