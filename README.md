# Du-IN Chinese word-reading sEEG (Zheng et al., NeurIPS 2024): the authors' preprocessed epochs

**These are not raw recordings.** This dataset is a BIDS packaging of the word-reading sEEG data released with
*Du-IN: Discrete units-guided mask modeling for decoding speech from Intracranial Neural signals* (Zheng, Wang, Jiang,
Chen, He, Lin, Wei, Zhao, Liu; NeurIPS 2024; doi:10.52202/079017-2542; arXiv:2405.11459). The authors published only
a preprocessed version of the 61-word reading data on Hugging Face (`liulab-repository/Du-IN`, revision
`2c85b670230dced33f2f1cbd0903648680ecc7d0`, last modified 2025-04-30, licence CC-BY-4.0). Their GitHub README says:
"we can only share the preprocessed version of the 61-word reading sEEG dataset (~3 hours)". The ~12 h of
non-task recordings used for pre-training are not shared. `dataset_description.json` therefore declares
`DatasetType: derivative`.

## Participants and task (from the paper, Appendix A)

- 12 patients with pharmacologically intractable epilepsy (9 male, 3 female; aged 15-53, mean 27.8, SD 10.4). The release
  does not link age or sex to individual subjects, so `participants.tsv` holds only the subject IDs. 7 to 13 sEEG
  electrodes per subject, placed for clinical reasons only. Recorded at 2000 Hz.
- Task: reading Chinese words aloud. The 61-word set and the authors' English translations are in the paper (Table 4)
  and in the `word_en` column of the events files. Each trial starts with the word in white text (0.5 s). The text
  then turns green, which is the go cue, and stays on screen for 2 s while the subject reads the word aloud. A
  fixation cross follows for 0.5 s. Each ~10-minute block presents every word twice in random order (122 trials).
  The paper reports 25 blocks in total.
- Ethics, as stated by the authors: "Experiments that contribute to this work were approved by IRB. All subjects
  consent to participate." The consent form includes a privacy statement and data retention "after deleting all
  personal identification information (PII)". The release contains no names, dates or imaging.

## Preprocessing done by the authors (before release)

Paper section 4.2: band-pass 0.5-200 Hz, 50 Hz notch, resampling to 1000 Hz, bipolar re-reference. The signals were
then cut into 3-s samples (3000 points), each labelled with its word. The released variant is named
`dataset.bipolar.default.unaligned`. The paper also lists per-channel z-scoring, but the stored values are not
z-scored: per-channel standard deviations are of order 1e-5. That step is presumably applied at training time.
The release does not state:
- the unit (the magnitudes are only plausible as volts, so `V` is used and the numbers are left unchanged);
- the contact pairing of each bipolar channel (channel names are as released);
- where each 3-s epoch sits relative to word onset, go cue or speech onset;
- whether the stored epoch order is the presentation order;
- electrode coordinates or anatomical labels. BIDS iEEG requires an electrodes file, so each subject's `electrodes.tsv`
  lists the released channel names with x, y, z and size set to `n/a`, and `coordsystem.json` says `Other` with no
  unit. No coordinates were estimated.

## Files

- `sub-<id>/ieeg/sub-<id>_task-wordreading_run-<n>_ieeg.vhdr/.vmrk/.eeg`: one file per source run
  (`word-recitation/run<n>`). BrainVision, IEEE float32, 1000 Hz, unit V, resolution 1. Each value is the authors'
  stored float64 value rounded to float32 (maximum absolute rounding error 1.5e-08 V). The epochs are
  stored **back to back**: the sidecar says `RecordingType: epoched` with `EpochLength: 3`, and the marker file has a
  `New Segment` at each epoch start. The time axis of the file is not the time axis of the original recording.
  Do not filter across epoch boundaries. To get epochs, split every 3000 samples.
  `mne_bids.read_raw_bids` refuses epoched recordings, so read the file with `mne.io.read_raw_brainvision` and reshape it.
- `..._events.tsv`: one row per epoch. `value` holds the word exactly as stored (UTF-8 Chinese) and `word_en` holds the
  authors' translation. `source_epoch_index` is the epoch's position in the source pickle.
- `..._channels.tsv`: all channels are `SEEG` with the authors' filter settings. `group` is the electrode shaft
  (the name prefix). All channels are `good`, since the release flags none.
- `sub-<id>_scans.tsv`: the source file behind each recording.
- `sourcedata/huggingface-liulab-repository-Du-IN/`: the original `data` and `info` files of every run, byte-identical
  (sha256 in `sourcedata/sourcedata_provenance.json`). **They are Python pickles.** Never call `pickle.load` on
  files you do not trust. `code/laneJ_pkl.py` is a restricted unpickler that admits only the globals these files use.
  Each `data` file is a list of records `{name: <word>, data_s: float64 array (n_channels, 3000)}`. Each `info`
  file holds `{ch_names: [...]}`. Model checkpoints (`pretrains/`) from the same release are not copied, because they
  are not recordings.
- `code/`: the download, conversion and round-trip scripts used to build this package.

## Recordings

| Subject | Runs | Channels | Epochs | Minutes of epochs | NaN values |
|---|---|---|---|---|---|
| sub-001 | 1, 2, 3, 4, 5, 6 | 104 | 3065 | 153.2 | 0 |
| sub-002 | 1, 2, 3, 4, 5, 6 | 115 | 3625 | 181.2 | 0 |
| sub-003 | 1, 2, 3, 4, 5, 6 | 67 | 3442 | 172.1 | 0 |
| sub-004 | 1, 3, 4, 5, 6 | 100 | 3043 | 152.2 | 0 |
| sub-005 | 1, 2, 3, 4, 5 | 123 | 3048 | 152.4 | 0 |
| sub-006 | 1, 2, 3, 4, 5, 6 | 101 | 3365 | 168.2 | 0 |
| sub-007 | 1, 2, 3, 4, 5, 6 | 94 | 3546 | 177.3 | 0 |
| sub-008 | 1, 2, 3, 4, 5, 6 | 98 | 3628 | 181.4 | 0 |
| sub-009 | 1, 2, 3, 4, 5, 6 | 147 | 3473 | 173.7 | 0 |
| sub-010 | 1, 2, 3, 4, 5, 6 | 88 | 3501 | 175.1 | 0 |
| sub-011 | 1, 2, 3, 4, 5, 6 | 90 | 3161 | 158.1 | 0 |
| sub-012 | 1, 2, 3 | 62 | 1830 | 91.5 | 0 |

Total: 67 runs, 38727 epochs (32.27 h).

Subject 004 has no run 2, subject 005 has no run 6, and subject 012 has only runs 1-3. This matches the release.
A full run would hold 610 epochs (5 blocks x 122 trials), but many runs hold fewer. The authors' loader explains why:
"The labels may not be the same, due to bad trials" (`utils/data/seeg/he2023xuanwu/word_recitation.py`). The removed
trials and the rejection criterion are not documented, and sub-009 run 5 has 60 of the 61 words. A few runs contain
large transients: the maximum |value| is 0.48 V in sub-003 run 3 and 0.24 V in sub-008 run 4, while median channel SDs
are about 2e-5 to 6e-5 V. These are kept as released, and no channel is marked bad.

## Conversion and checks

Packaging only: no filtering, resampling, re-referencing, channel dropping or epoch dropping. A round trip
read every file back with MNE and compared it with the source pickles. All samples were equal to float32(source),
and channel order, epoch count, words, onsets and durations matched in all 67 runs. The BIDS validator reported
no errors. Packaged for NEMAR by Bruno Aristimunha (2026-10-06).

## Licence and citation

Licence: CC-BY-4.0 (Hugging Face dataset card of `liulab-repository/Du-IN`). The Du-IN code on GitHub is MIT licensed.
If you use these data, cite:

Zheng H, Wang H-T, Jiang W-B, Chen Z-T, He L, Lin P-Y, Wei P-H, Zhao G-G, Liu Y-Z. Du-IN: Discrete units-guided mask
modeling for decoding speech from Intracranial Neural signals. NeurIPS 2024. doi:10.52202/079017-2542, arXiv:2405.11459.
