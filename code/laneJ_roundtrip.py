#!/usr/bin/env python3
"""Lane J (IEEG033): round-trip check of one converted subject against the source pickles.

laneJ_roundtrip.py <bids_dir> <NNN> -> reports-<bids>/roundtrip_sub-NNN.json; exit 1 on any mismatch.
Reads the BrainVision files with MNE (independent reader), compares every sample to float32(source), channel order,
duration, epoch count, events (word per epoch, onsets), channel units and sidecar counts.
"""
import csv
import json
import sys
from pathlib import Path

import mne
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import laneJ_pkl  # noqa: E402

bids, sub = Path(sys.argv[1]), sys.argv[2]
src = bids / 'sourcedata/huggingface-liulab-repository-Du-IN/data/seeg.he2023xuanwu' / sub / 'word-recitation'
res, ok = {}, True
for rd in sorted(p for p in src.iterdir() if p.is_dir()):
    run = int(rd.name[3:])
    ds = rd / 'dataset.bipolar.default.unaligned'
    info = laneJ_pkl.load(ds / 'info')
    items = laneJ_pkl.load(ds / 'data')
    base = bids / f'sub-{sub}/ieeg/sub-{sub}_task-wordreading_run-{run}'
    raw = mne.io.read_raw_brainvision(f'{base}_ieeg.vhdr', preload=True, verbose='error')
    x = raw.get_data()  # volts (unit V, resolution 1 -> scale 1)
    ref = np.concatenate([d['data_s'] for d in items], axis=1).astype(np.float32).astype(np.float64)
    with open(f'{base}_events.tsv', encoding='utf-8') as f:
        ev = list(csv.DictReader(f, delimiter='\t'))
    with open(f'{base}_channels.tsv', encoding='utf-8') as f:
        chs = list(csv.DictReader(f, delimiter='\t'))
    sc = json.loads(Path(f'{base}_ieeg.json').read_text())
    r = {
        'channels_equal': raw.ch_names == list(info['ch_names']) == [c['name'] for c in chs],
        'n_times_equal': x.shape == ref.shape,
        'samples_exact': bool(x.shape == ref.shape and np.array_equal(x, ref)),
        'max_abs_diff_vs_float64_source': float(np.max(np.abs(x - np.concatenate([d['data_s'] for d in items], axis=1)))) if x.shape == ref.shape else None,
        'sfreq': float(raw.info['sfreq']),
        'duration_s': float(raw.n_times / raw.info['sfreq']),
        'sidecar_duration_equal': bool(abs(sc['RecordingDuration'] - raw.n_times / raw.info['sfreq']) < 1e-9),
        'sidecar_channel_count_equal': sc['SEEGChannelCount'] == len(raw.ch_names),
        'events_words_equal': [e['value'] for e in ev] == [d['name'] for d in items],
        'events_onsets_ok': all(abs(float(e['onset']) - 3.0 * k) < 1e-9 and int(e['sample']) == 3000 * k for k, e in enumerate(ev)),
        'segments_in_vmrk': sum(1 for a in raw.annotations if a['description'].startswith('New Segment')) if len(raw.annotations) else 0,
        'units_V': all(c['units'] == 'V' for c in chs),
        'epochs': len(items),
    }
    r['segments_note'] = 'MNE turns each New Segment marker except the one at sample 0 into an annotation; expected epochs - 1'
    r['segments_ok'] = r['segments_in_vmrk'] == len(items) - 1
    r['pass'] = all(r[k] for k in ('channels_equal', 'n_times_equal', 'samples_exact', 'sidecar_duration_equal',
                                   'sidecar_channel_count_equal', 'events_words_equal', 'events_onsets_ok', 'units_V', 'segments_ok'))
    ok &= r['pass']
    res[run] = r
    print(run, r, flush=True)
out = bids.parent / f'reports-{bids.name}' / f'roundtrip_sub-{sub}.json'
out.write_text(json.dumps({'subject': sub, 'pass': ok, 'runs': res}, indent=1) + '\n')
sys.exit(0 if ok else 1)
