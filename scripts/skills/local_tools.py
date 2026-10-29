"""Deterministic local helpers. No network, inference or publication."""
import argparse
import hashlib
import re
import statistics
import json
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2] / 'tools/choms-skills'
FIELDS = ('purpose', 'audience', 'primary_action')
LISTS = ('preserve', 'references', 'acceptance')


def validate_brief(value):
    if not isinstance(value, dict):
        raise ValueError('brief_object_required')
    if set(value) != set(FIELDS + LISTS):
        raise ValueError('brief_fields')
    for key in FIELDS:
        if not isinstance(value[key], str) or not value[key].strip():
            raise ValueError('brief_text_required:' + key)
    for key in LISTS:
        if not isinstance(value[key], list) or not value[key]:
            raise ValueError('brief_nonempty_list_required:' + key)
        if any(not isinstance(x, str) or not x.strip() for x in value[key]):
            raise ValueError('brief_list_text_required:' + key)
    return {'valid': True, 'acceptance_checks': len(value['acceptance'])}


class StructuralLint(HTMLParser):
    """Deliberately narrow: findings, never accessibility certification."""
    def __init__(self):
        super().__init__()
        self.findings = []
        self.lang = False
        self.title = False
        self.main = False
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'html':
            self.lang = bool(a.get('lang'))
        self.title |= tag == 'title'
        self.main |= tag == 'main'
        if tag == 'img' and 'alt' not in a:
            self.findings.append('image_missing_alt')
        if tag == 'img' and not all(a.get(k) for k in ('width', 'height')):
            self.findings.append('image_missing_dimensions')
        if tag == 'input' and a.get('type') != 'hidden' and not a.get('id'):
            self.findings.append('input_missing_id')
        if a.get('id'):
            if a['id'] in self.ids:
                self.findings.append('duplicate_id')
            self.ids.add(a['id'])

    def result(self):
        return {'scope': 'structural HTML only; browser/manual review required',
                'findings': sorted(set(self.findings + [name for ok, name in
                    ((self.lang, 'missing_lang'), (self.title, 'missing_title'),
                     (self.main, 'missing_main')) if not ok]))}


def media(path, ffprobe):
    result = subprocess.run([ffprobe, '-v', 'error', '-show_entries',
        'format=duration:stream=codec_type,width,height,r_frame_rate',
        '-of', 'json', str(path.resolve())], capture_output=True, timeout=30)
    if result.returncode:
        raise ValueError('ffprobe_failed')  # No user tags, filenames or stderr.
    value = json.loads(result.stdout)
    videos = [s for s in value.get('streams', []) if s.get('codec_type') == 'video']
    duration = float(value.get('format', {}).get('duration', 0))
    if not videos or not 0 < duration < 86400:
        raise ValueError('video_or_duration_invalid')
    video = videos[0]
    if not all(isinstance(video.get(k), int) and video[k] > 0 for k in ('width', 'height')):
        raise ValueError('video_dimensions_invalid')
    return {'valid': True, 'duration_seconds': duration, 'width': video['width'],
            'height': video['height'], 'fps': video.get('r_frame_rate'),
            'audio_streams': sum(s.get('codec_type') == 'audio' for s in value['streams']),
            'publication': False}


def measure_video(path, genre, ffmpeg, ffprobe):
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,47}', genre):
        raise ValueError('genre_slug_required')
    info = media(path, ffprobe)
    result = subprocess.run([ffmpeg, '-nostdin', '-hide_banner', '-loglevel', 'error', '-i', str(path.resolve()),
        '-vf', 'fps=1,signalstats,metadata=print:file=-', '-an', '-f', 'null', '-'],
        capture_output=True, text=True, timeout=300)
    if result.returncode:
        raise ValueError('measurement_failed')
    stats = {}
    for key in ('YAVG', 'UAVG', 'VAVG'):
        values = [float(v) for v in re.findall(r'lavfi\.signalstats\.' + key + r'=([0-9.]+)', result.stdout)]
        if not values:
            raise ValueError('measurement_missing_samples')
        stats[key] = {'mean': statistics.fmean(values), 'samples': len(values)}
    with path.open('rb') as source:
        digest = hashlib.file_digest(source, 'sha256').hexdigest()
    return {'schema': 'choms-video-measurements-v1', 'genre': genre, 'source_sha256': digest,
            'duration_seconds': info['duration_seconds'], 'sample_fps': 1,
            'signalstats': stats, 'scope': 'sampled encoded YUV statistics; no perceptual grade, LUT or cadence inferred',
            'inferences': 0, 'publication': False}


def export_video(source, destination, width, height, ffmpeg, ffprobe):
    if destination.exists() or destination.is_symlink() or source.resolve() == destination.resolve():
        raise ValueError('output_exists')
    if destination.suffix.lower() != '.mp4':
        raise ValueError('mp4_output_required')
    if any(n <= 0 or n > 3840 or n % 2 for n in (width, height)):
        raise ValueError('even_dimensions_up_to_3840_required')
    media(source, ffprobe)  # Reject invalid input before rendering.
    result = subprocess.run([ffmpeg, '-nostdin', '-hide_banner', '-loglevel', 'error', '-n',
        '-i', str(source.resolve()), '-map', '0:v:0', '-map', '0:a?', '-vf',
        f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2',
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-map_metadata', '-1',
        '-movflags', '+faststart', str(destination.resolve())], capture_output=True, timeout=300)
    if result.returncode:
        raise ValueError('export_failed_partial_output_may_exist')
    value = media(destination, ffprobe)
    if (value['width'], value['height']) != (width, height):
        raise ValueError('export_dimensions_mismatch')
    return value | {'exported': True, 'framing': 'fit-and-pad; no crop', 'publication': False}


def find(query):
    tokens = set(query.lower().split())
    entries = json.loads((ROOT / 'CANDIDATES.json').read_text())['candidates']
    scored = [(len(tokens & set((e['name'] + ' ' + e['keywords']).lower().split())), e) for e in entries]
    return [e for score, e in sorted(scored, key=lambda x: (-x[0], x[1]['name'])) if score]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('find').add_argument('query', nargs='+')
    sub.add_parser('brief').add_argument('path', type=Path)
    sub.add_parser('html').add_argument('path', type=Path)
    m = sub.add_parser('media'); m.add_argument('path', type=Path); m.add_argument('--ffprobe', default='ffprobe')
    t = sub.add_parser('measure'); t.add_argument('path', type=Path); t.add_argument('--genre', required=True)
    t.add_argument('--ffmpeg', default='ffmpeg'); t.add_argument('--ffprobe', default='ffprobe')
    e = sub.add_parser('export'); e.add_argument('path', type=Path); e.add_argument('destination', type=Path)
    e.add_argument('--width', type=int, required=True); e.add_argument('--height', type=int, required=True)
    e.add_argument('--ffmpeg', default='ffmpeg'); e.add_argument('--ffprobe', default='ffprobe')
    args = parser.parse_args()
    try:
        if args.command == 'find':
            value = find(' '.join(args.query))
        elif args.command == 'brief':
            value = validate_brief(json.loads(args.path.read_text()))
        elif args.command == 'html':
            lint = StructuralLint(); lint.feed(args.path.read_text()); value = lint.result()
        elif args.command == 'measure':
            value = measure_video(args.path, args.genre, args.ffmpeg, args.ffprobe)
        elif args.command == 'export':
            value = export_video(args.path, args.destination, args.width, args.height, args.ffmpeg, args.ffprobe)
        else:
            value = media(args.path, args.ffprobe)
        print(json.dumps(value, ensure_ascii=False, sort_keys=True))
        return 1 if isinstance(value, dict) and value.get('findings') else 0
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({'error': type(exc).__name__, 'status': 'FAIL'}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
