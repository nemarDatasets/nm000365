#!/usr/bin/env python3
"""Lane J (IEEG033): BIDS packaging of the Du-IN word-reading sEEG release (Hugging Face liulab-repository/Du-IN).

  laneJ_convert.py sub <NNN> <out_dir>   one subject: BrainVision + sidecars per run, source pickles copied to sourcedata/
  laneJ_convert.py top <out_dir>         dataset-level files (templates, participants, inherited sidecars, provenance, code/)

No signal processing. The release holds, per run, a pickled list of 3-s epochs (data_s: n_channels x 3000 float64, name: the
word) and a channel-name list. Epochs are written back to back to one BrainVision IEEE float32 file per run
(RecordingType epoched, EpochLength 3 s, resolution 1, so the file value equals the stored float64 rounded to float32).
The float64 originals are copied byte-identically to sourcedata/ (sha256 checked against the acquisition receipt).
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import laneJ_pkl  # noqa: E402

ROOT = Path('/voyager/ceph/groups/sdp190/bpinto/ieeg-nemar-20261005')
import os
W = Path(os.environ.get('LANEJ_WORK', str(ROOT / 'work/IEEG033')))
HF = W / 'sourcedata/huggingface-liulab-repository-Du-IN'
SRCREL = 'sourcedata/huggingface-liulab-repository-Du-IN'
TASK = 'wordreading'
FS = 1000.0
CONVERTER = 'laneJ_convert.py (ieeg-nemar-20261005 campaign, lane J)'

# Paper (arXiv 2405.11459v3, Appendix A, Table 4): the 61 words and the authors' English translations, verbatim.
WORDS_EN = {
    '嘴巴': 'mouth', '菠萝': 'pineapple', '帮助': 'help', '把': 'get', '朋友': 'friend', '脸盆': 'washbasin',
    '平静': 'calm', '漂亮': 'pretty', '衣服': 'clothes', '豆腐': 'tofu', '米饭': 'rice', '放在': 'put on',
    '面条': 'noodle', '毛巾': 'towel', '关门': 'close the door', '电脑': 'computer', '凳子': 'stool', '小刀': 'knife',
    '头疼': 'headache', '软糖': 'gummies', '醋': 'vinegar', '青菜': 'vegetables', '厕所': 'toilet', '葱花': 'chopped green onion',
    '手机': 'cell phone', '篮球': 'basketball', '钢琴': 'piano', '心情': 'mood', '丝瓜': 'loofah', '蒜泥': 'garlic paste',
    '怎样': 'how', '香肠': 'sausage', '需要': 'need', '你': 'you', '拿': 'hold', '橙汁': 'orange juice',
    '找': 'look for', '猪肉': 'pork', '吃': 'eat', '穿': 'wear', '是': 'be', '家人': 'family',
    '热水': 'hot water', '护士': 'nurse', '换药': 'change dressing', '喝': 'drink', '口渴': 'thirsty', '看': 'look',
    '碗': 'bowl', '鱼块': 'steak', '感觉': 'feel', '给': 'give', '玩': 'play', '问题': 'problem',
    '外卖': 'takeouts', '有': 'have', '音乐': 'music', '预约': 'reserve', '汤圆': 'sweet dumpling', '愿意': 'willing',
    '我': 'I',
}
assert len(WORDS_EN) == 61


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def wjson(p, d):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def wtsv(p, cols, rows):
    p.parent.mkdir(parents=True, exist_ok=True)

    def fmt(v):
        if v is None:
            return 'n/a'
        if isinstance(v, (float, np.floating)):
            return repr(float(v)) if np.isfinite(v) else 'n/a'
        return str(v)
    p.write_text('\n'.join(['\t'.join(cols)] + ['\t'.join(fmt(r[c]) for c in cols) for r in rows]) + '\n', encoding='utf-8')


def write_brainvision(base, data, ch_names, unit, n_per_epoch):
    base.parent.mkdir(parents=True, exist_ok=True)
    stem = base.name
    with open(base.with_suffix('.eeg'), 'wb') as f:
        for ep in data:  # ep: (n_channels, n_per_epoch) float64 -> multiplexed float32
            f.write(np.ascontiguousarray(ep.T.astype('<f4')).tobytes())
    chl = '\n'.join(f'Ch{i + 1}={n.replace(",", chr(92) + "1")},,1,{unit}' for i, n in enumerate(ch_names))
    base.with_suffix('.vhdr').write_text(
        'Brain Vision Data Exchange Header File Version 1.0\n'
        f'; Written by {CONVERTER}: authors\' stored values (float64 -> float32), resolution 1; epochs back to back\n\n'
        '[Common Infos]\nCodepage=UTF-8\n'
        f'DataFile={stem}.eeg\nMarkerFile={stem}.vmrk\nDataFormat=BINARY\nDataOrientation=MULTIPLEXED\n'
        f'NumberOfChannels={len(ch_names)}\nSamplingInterval={1e6 / FS:.10g}\n\n'
        '[Binary Infos]\nBinaryFormat=IEEE_FLOAT_32\n\n'
        '[Channel Infos]\n; Each entry: Ch<Channel number>=<Name>,<Reference channel name>,<Resolution in "Unit">,<Unit>\n'
        f'{chl}\n', encoding='utf-8')
    mk = ['Brain Vision Data Exchange Marker File, Version 1.0\n\n[Common Infos]\nCodepage=UTF-8\n',
          f'DataFile={stem}.eeg\n\n[Marker Infos]\n',
          '; Each entry: Mk<Marker number>=<Type>,<Description>,<Position in data points>,<Size in data points>,<Channel number (0 = marker is related to all channels)>\n']
    for k in range(len(data)):
        mk.append(f'Mk{k + 1}=New Segment,,{k * n_per_epoch + 1},1,0\n')
    base.with_suffix('.vmrk').write_text(''.join(mk), encoding='utf-8')


def group_of(n):
    return n.rstrip('0123456789')


def receipt_map():
    r = json.loads((W / 'acquisition_receipt.json').read_text())
    assert r['complete'], 'acquisition receipt not complete'
    return {f['path']: f for f in r['files']}


def convert_sub(src_sub, out):
    rec = receipt_map()
    sub = src_sub  # BIDS label = source subject id (001..012)
    task_dir = HF / 'data/seeg.he2023xuanwu' / src_sub / 'word-recitation'
    runs = sorted((p for p in task_dir.iterdir() if p.is_dir()), key=lambda p: int(p.name[3:]))
    summary = {'subject': sub, 'runs': {}}
    scans = []
    for rd in runs:
        run = int(rd.name[3:])
        ds = rd / 'dataset.bipolar.default.unaligned'
        info = laneJ_pkl.load(ds / 'info')
        items = laneJ_pkl.load(ds / 'data')
        ch = list(info['ch_names'])
        assert len(set(ch)) == len(ch), 'duplicate channel names'
        assert all(set(d.keys()) == {'data_s', 'name'} for d in items), 'unexpected epoch fields'
        shapes = {d['data_s'].shape for d in items}
        assert shapes == {(len(ch), 3000)}, shapes
        assert all(d['data_s'].dtype == np.float64 for d in items)
        words = [d['name'] for d in items]
        assert set(words) <= set(WORDS_EN), set(words) - set(WORDS_EN)
        arrs = [d['data_s'] for d in items]
        nan = int(sum(int(np.isnan(a).sum()) for a in arrs))
        allx = np.concatenate(arrs, axis=1)
        ch_std = allx.std(axis=1)
        ch_mean = allx.mean(axis=1)
        maxerr = float(np.max(np.abs(allx.astype(np.float32).astype(np.float64) - allx)))
        n_per = 3000
        base = out / f'sub-{sub}' / 'ieeg' / f'sub-{sub}_task-{TASK}_run-{run}_ieeg'
        write_brainvision(base, arrs, ch, 'V', n_per)
        ev = [{'onset': k * 3.0, 'duration': 3.0, 'sample': k * n_per, 'trial_type': 'word_epoch', 'value': w,
               'word_en': WORDS_EN[w], 'source_epoch_index': k} for k, w in enumerate(words)]
        wtsv(base.parent / f'sub-{sub}_task-{TASK}_run-{run}_events.tsv',
             ['onset', 'duration', 'sample', 'trial_type', 'value', 'word_en', 'source_epoch_index'], ev)
        rows = [{'name': n, 'type': 'SEEG', 'units': 'V', 'low_cutoff': 0.5, 'high_cutoff': 200.0, 'notch': 50.0,
                 'group': group_of(n), 'status': 'good', 'status_description': 'n/a'} for n in ch]
        wtsv(base.parent / f'sub-{sub}_task-{TASK}_run-{run}_channels.tsv',
             ['name', 'type', 'units', 'low_cutoff', 'high_cutoff', 'notch', 'group', 'status', 'status_description'], rows)
        wjson(base.with_suffix('.json'), {
            'TaskName': TASK,
            'TaskDescription': ('Chinese word reading aloud (source task name "word-recitation"). Each trial: a word from a fixed 61-word set '
                                'appears in white (0.5 s), turns green (go cue, 2 s; the subject reads it aloud), then a fixation cross (0.5 s). '
                                'Each ~10-min block presents every word twice in randomised order (122 trials).'),
            'Instructions': 'Speak the word aloud as soon as the text turns green (paraphrase of the paper, Appendix A).',
            'SamplingFrequency': FS,
            'PowerLineFrequency': 50,
            'SoftwareFilters': {
                'band-pass (authors)': {'low_cutoff_Hz': 0.5, 'high_cutoff_Hz': 200},
                'notch (authors)': {'frequency_Hz': 50},
                'resampling (authors)': {'from_Hz': 2000, 'to_Hz': 1000},
                'bipolar re-reference (authors)': {'description': 'bi-polar re-referencing as stated in the paper; the contact pairing is not encoded in the release'},
            },
            'HardwareFilters': 'n/a',
            'iEEGReference': 'Bipolar re-reference applied by the authors (paper section 4.2). Channel names are as released; the pairing of each channel is not stated.',
            'SEEGChannelCount': len(ch), 'ECOGChannelCount': 0, 'EEGChannelCount': 0, 'EOGChannelCount': 0,
            'ECGChannelCount': 0, 'EMGChannelCount': 0, 'MiscChannelCount': 0, 'TriggerChannelCount': 0,
            'RecordingType': 'epoched',
            'EpochLength': 3.0,
            'RecordingDuration': len(items) * 3.0,
            'iEEGGround': 'n/a',
            'iEEGPlacementScheme': 'Clinically determined sEEG depth electrodes (7-13 electrodes per subject according to the paper).',
            'ElectricalStimulation': False,
        })
        scans.append({'filename': f'ieeg/{base.name}.vhdr', 'source_file': f'{SRCREL}/data/seeg.he2023xuanwu/{src_sub}/word-recitation/{rd.name}/dataset.bipolar.default.unaligned/data'})
        # byte copy of the source pickles
        for fn in ('data', 'info'):
            rel = f'data/seeg.he2023xuanwu/{src_sub}/word-recitation/{rd.name}/dataset.bipolar.default.unaligned/{fn}'
            dst = out / SRCREL / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(HF / rel, dst)
            h = sha256(dst)
            assert h == rec[rel]['sha256'], f'sha256 mismatch {rel}'
        summary['runs'][run] = {
            'epochs': len(items), 'channels': len(ch), 'words': len(set(words)), 'nan_values': nan,
            'channel_std_median': float(np.median(ch_std)), 'channel_std_min': float(ch_std.min()), 'channel_std_max': float(ch_std.max()),
            'channel_mean_abs_max': float(np.abs(ch_mean).max()), 'abs_max': float(np.abs(allx).max()),
            'max_abs_float32_error': maxerr, 'word_counts': {w: words.count(w) for w in sorted(set(words))}}
    wtsv(out / f'sub-{sub}' / f'sub-{sub}_scans.tsv', ['filename', 'source_file'], scans)
    rep = out.parent / f'reports-{out.name}'
    rep.mkdir(exist_ok=True)
    wjson(rep / f'convert_sub-{sub}.json', summary)
    print(json.dumps({r: {k: v for k, v in s.items() if k != 'word_counts'} for r, s in summary['runs'].items()}, indent=1))


def convert_top(out):
    tpl = Path(__file__).with_name('laneJ_ieeg033_templates')
    for p in tpl.iterdir():
        shutil.copyfile(p, out / p.name)
    subs = sorted(p.name for p in (HF / 'data/seeg.he2023xuanwu').iterdir())
    wtsv(out / 'participants.tsv', ['participant_id', 'source_subject_id'], [{'participant_id': f'sub-{s}', 'source_subject_id': s} for s in subs])
    wjson(out / 'participants.json', {'source_subject_id': {'Description': 'Subject directory name in the Hugging Face release (data/seeg.he2023xuanwu/<id>).'}})
    wjson(out / f'task-{TASK}_events.json', {
        'onset': {'Description': 'Seconds from the start of this file. The file holds the authors\' 3-s epochs back to back (RecordingType epoched); onsets are NOT times in the original continuous recording, which is not shared.', 'Units': 's'},
        'duration': {'Description': 'Epoch length (3000 samples at 1000 Hz).', 'Units': 's'},
        'sample': {'Description': '0-based sample index of the epoch start in this file.'},
        'trial_type': {'Levels': {'word_epoch': 'One 3-s epoch of the authors\' word-reading samples ("dataset.bipolar.default.unaligned").'}},
        'value': {'Description': 'The word the subject read aloud in this trial, exactly as stored in the release (field "name", UTF-8 Chinese). One of 61 words.'},
        'word_en': {'Description': 'English translation of the word as given by the authors in the paper (arXiv 2405.11459v3, Appendix A, Table 4).'},
        'source_epoch_index': {'Description': '0-based position of the epoch in the source pickled list (dataset.bipolar.default.unaligned/data). The release does not state whether this order is the presentation order, and does not give the position of the epoch relative to the trial events (word onset, go cue, speech onset); "unaligned" is the authors\' variant name.'},
    })
    wjson(out / f'task-{TASK}_channels.json', {
        'units': {'Description': 'The release has no unit field. The stored values (per-channel standard deviation of order 1e-5) are only plausible as volts, so V is used; the numbers are exactly the authors\' stored values (float32-rounded). They are NOT z-scored, although the paper lists per-channel z-scoring as a preprocessing step (presumably applied at training time).'},
        'low_cutoff': {'Description': 'High-pass edge of the authors\' 0.5-200 Hz band-pass (paper section 4.2).', 'Units': 'Hz'},
        'high_cutoff': {'Description': 'Low-pass edge of the authors\' 0.5-200 Hz band-pass.', 'Units': 'Hz'},
        'notch': {'Description': '50 Hz notch applied by the authors (value in Hz).'},
        'group': {'Description': 'Electrode shaft: channel-name prefix before the contact number, as released.'},
    })
    for sd in sorted(out.glob('sub-*')):
        sub = sd.name[4:]
        names = []
        for ct in sorted((sd / 'ieeg').glob('*_channels.tsv')):
            for line in ct.read_text(encoding='utf-8').splitlines()[1:]:
                n = line.split('\t')[0]
                if n not in names:
                    names.append(n)
        wtsv(sd / 'ieeg' / f'sub-{sub}_electrodes.tsv', ['name', 'x', 'y', 'z', 'size', 'group'],
             [{'name': n, 'x': None, 'y': None, 'z': None, 'size': None, 'group': group_of(n)} for n in names])
        wjson(sd / 'ieeg' / f'sub-{sub}_electrodes.json', {
            'name': {'Description': 'Channel names exactly as released (bipolar derivations named by the authors; the contact pairing is not stated). Listed because BIDS iEEG requires an electrodes file; no coordinates were released, so x, y, z and size are n/a. Nothing was estimated.'},
            'group': {'Description': 'Electrode shaft: name prefix before the contact number.'},
        })
        wjson(sd / 'ieeg' / f'sub-{sub}_coordsystem.json', {
            'iEEGCoordinateSystem': 'Other',
            'iEEGCoordinateUnits': 'n/a',
            'iEEGCoordinateSystemDescription': 'No electrode coordinates or anatomical labels are included in the Du-IN release (Hugging Face liulab-repository/Du-IN); x, y, z in electrodes.tsv are n/a.',
        })
        wjson(sd / f'sub-{sub}_scans.json', {'source_file': {'Description': 'Path (within this dataset) of the original pickled epochs file the recording was packaged from.'}})
    code = out / 'code'
    code.mkdir(exist_ok=True)
    for f in ('laneJ_convert.py', 'laneJ_pkl.py', 'laneJ_hf_acquire.py', 'laneJ_roundtrip.py'):
        shutil.copyfile(Path(__file__).with_name(f), code / f)
    for f in ('README.md', '.gitattributes'):
        (out / SRCREL).mkdir(parents=True, exist_ok=True)
        shutil.copyfile(HF / f, out / SRCREL / f)
    r = json.loads((W / 'acquisition_receipt.json').read_text())
    wjson(out / 'sourcedata' / 'sourcedata_provenance.json', {
        'source': 'https://huggingface.co/datasets/liulab-repository/Du-IN', 'revision': r['revision'],
        'license': 'CC-BY-4.0 (Hugging Face dataset card)',
        'copied': 'All data/ pickles (data + info per run), README.md, .gitattributes, byte-identical, sha256 checked against the acquisition receipt.',
        'not_copied': {'pretrains/': 'Model checkpoints (PyTorch pickles) and training parameters of the Du-IN models: not recordings. Available from the same Hugging Face revision.'},
        'warning': 'The data/info files are Python pickles. Do not unpickle untrusted files with pickle.load; code/laneJ_pkl.py is a restricted unpickler that only admits the globals these files use.',
        'files': [{k: f[k] for k in ('path', 'size', 'sha256')} for f in r['files'] if f['path'].startswith('data/') or f['path'] in ('README.md', '.gitattributes')],
    })


if __name__ == '__main__':
    if sys.argv[1] == 'sub':
        out = Path(sys.argv[3])
        out.mkdir(parents=True, exist_ok=True)
        if (out / f'sub-{sys.argv[2]}').exists():
            raise SystemExit('subject already converted')
        convert_sub(sys.argv[2], out)
    else:
        convert_top(Path(sys.argv[2]))
