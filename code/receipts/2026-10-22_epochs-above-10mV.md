# Flag epochs with transients above 10 mV

**Claim**: 55 epochs in 16 runs have |value| > 10 mV (median epoch maximum 0.53 mV); they are marked `bad` in
`events.tsv` with channel and peak in `status_description` (PR nemarDatasets/nm000365#3, head
`a41527de49a5dc7d595555ee4f1da0573f26c3de`).

**Source**
- NEMAR nm000365 at `origin/main` `d4f8bf28b6cca6130f48c6efbc1c289bba42ce9d`: all 67 runs
  `sub-*/ieeg/*_task-wordreading_run-*_ieeg.{vhdr,eeg}` and their `events.tsv`. Identification: sha256 of each annexed
  file read (67 `.vhdr`, 67 `.eeg`) equals its SHA256E git-annex key at that commit; the 67 `events.tsv` equal the git blobs.
- Upstream: Hugging Face dataset `liulab-repository/Du-IN`, revision `2c85b670230dced33f2f1cbd0903648680ecc7d0`, the
  `data` and `info` pickles (`dataset.bipolar.default.unaligned`) of the 16 runs with a flagged epoch, downloaded from that
  revision; the sha256 of all 32 files equals `sourcedata/sourcedata_provenance.json`.

**Method**
- Reader: numpy on the BrainVision binary (IEEE_FLOAT_32, multiplexed, resolution 1, unit V: the authors' float64 values
  stored as float32, no scaling).
- Epochs: the `events.tsv` rows, 3.0 s = 3000 samples at 1000 Hz, back to back (checked: `sample` = row x 3000).
- Per epoch and channel: max |value|. An epoch is bad if a channel exceeds 10 mV (0.01 V); `status_description` lists
  those channels by decreasing peak, in mV with one decimal.
- Median over all epochs of the epoch maximum (max over channels).
- Upstream check: pickles read with a restricted unpickler (only numpy array reconstruction and the authors' `DotDict`);
  each epoch's `data_s` (channels x 3000, float64), taken at `source_epoch_index`, is compared with the BIDS epoch:
  max |HF - BIDS| over all samples, and the bad epochs and `status_description` recomputed from the HF values.

**Result**

| quantity | value |
|---|---|
| runs | 67 |
| epochs | 38727 |
| median epoch max abs value (all channels) | 0.53 mV |
| epochs with max abs value > 10 mV (status bad) | 55 in 16 runs |

| run | bad source_epoch_index |
|---|---|
| sub-001 run 2 | 128, 287, 289, 293, 296, 364 |
| sub-001 run 3 | 346, 392 |
| sub-001 run 4 | 72, 271, 365, 495, 532, 534, 542, 543 |
| sub-001 run 5 | 99 |
| sub-001 run 6 | 174, 175, 196, 257, 343, 387, 413, 435 |
| sub-003 run 3 | 535, 536 |
| sub-003 run 6 | 337 |
| sub-005 run 3 | 104 |
| sub-005 run 4 | 93, 382, 402, 475 |
| sub-005 run 5 | 320, 341 |
| sub-008 run 1 | 347, 399, 400 |
| sub-008 run 3 | 61, 77, 288, 365, 450, 508 |
| sub-008 run 4 | 405, 421, 514 |
| sub-008 run 5 | 192, 372, 487, 489 |
| sub-008 run 6 | 29, 35, 79 |
| sub-009 run 4 | 342 |

| run | source_epoch_index | onset (s) | status_description |
|---|---:|---:|---|
| sub-001 run 2 | 128 | 384.0 | transient > 10 mV: AN10 17.2 mV, AN11 17.1 mV, AN1 16.9 mV |
| sub-001 run 2 | 287 | 861.0 | transient > 10 mV: TI11 22.9 mV |
| sub-001 run 2 | 289 | 867.0 | transient > 10 mV: TI11 18.1 mV |
| sub-001 run 2 | 293 | 879.0 | transient > 10 mV: TI11 18.6 mV |
| sub-001 run 2 | 296 | 888.0 | transient > 10 mV: TI11 14.2 mV |
| sub-001 run 2 | 364 | 1092.0 | transient > 10 mV: TI11 66.9 mV |
| sub-001 run 3 | 346 | 1038.0 | transient > 10 mV: TI3 10.3 mV, TI2 10.3 mV |
| sub-001 run 3 | 392 | 1176.0 | transient > 10 mV: TI11 10.2 mV |
| sub-001 run 4 | 72 | 216.0 | transient > 10 mV: TA9 13.8 mV, TA8 13.8 mV |
| sub-001 run 4 | 271 | 813.0 | transient > 10 mV: AN1 19.0 mV, AN11 18.9 mV, AN10 18.8 mV |
| sub-001 run 4 | 365 | 1095.0 | transient > 10 mV: TI3 10.3 mV, TI2 10.3 mV |
| sub-001 run 4 | 495 | 1485.0 | transient > 10 mV: TI2 10.9 mV, TI3 10.9 mV |
| sub-001 run 4 | 532 | 1596.0 | transient > 10 mV: AN1 15.6 mV, AN10 14.4 mV, AN11 14.0 mV |
| sub-001 run 4 | 534 | 1602.0 | transient > 10 mV: TI2 11.0 mV, TI3 11.0 mV |
| sub-001 run 4 | 542 | 1626.0 | transient > 10 mV: TA9 10.7 mV, TA8 10.6 mV |
| sub-001 run 4 | 543 | 1629.0 | transient > 10 mV: AN1 10.6 mV, AN11 10.6 mV, AN10 10.6 mV |
| sub-001 run 5 | 99 | 297.0 | transient > 10 mV: AN10 15.6 mV, AN11 15.5 mV, AN1 15.4 mV |
| sub-001 run 6 | 174 | 522.0 | transient > 10 mV: TI11 10.4 mV |
| sub-001 run 6 | 175 | 525.0 | transient > 10 mV: AN10 18.4 mV, AN11 18.4 mV, AN1 17.8 mV |
| sub-001 run 6 | 196 | 588.0 | transient > 10 mV: TI11 19.6 mV |
| sub-001 run 6 | 257 | 771.0 | transient > 10 mV: TI11 11.7 mV |
| sub-001 run 6 | 343 | 1029.0 | transient > 10 mV: AN1 16.4 mV, AN10 16.3 mV, AN11 16.1 mV |
| sub-001 run 6 | 387 | 1161.0 | transient > 10 mV: AN1 19.4 mV, AN10 18.7 mV, AN11 18.4 mV |
| sub-001 run 6 | 413 | 1239.0 | transient > 10 mV: AN10 19.1 mV, AN11 19.1 mV, AN1 18.7 mV |
| sub-001 run 6 | 435 | 1305.0 | transient > 10 mV: AN1 14.4 mV, AN10 13.6 mV, AN11 13.5 mV |
| sub-003 run 3 | 535 | 1605.0 | transient > 10 mV: TH6 484.9 mV, TH5 484.9 mV |
| sub-003 run 3 | 536 | 1608.0 | transient > 10 mV: TH6 409.5 mV, TH5 409.4 mV |
| sub-003 run 6 | 337 | 1011.0 | transient > 10 mV: TH2 10.1 mV |
| sub-005 run 3 | 104 | 312.0 | transient > 10 mV: I11 12.7 mV |
| sub-005 run 4 | 93 | 279.0 | transient > 10 mV: I11 17.5 mV |
| sub-005 run 4 | 382 | 1146.0 | transient > 10 mV: I11 10.9 mV |
| sub-005 run 4 | 402 | 1206.0 | transient > 10 mV: I11 10.5 mV |
| sub-005 run 4 | 475 | 1425.0 | transient > 10 mV: I11 16.8 mV |
| sub-005 run 5 | 320 | 960.0 | transient > 10 mV: I11 11.6 mV |
| sub-005 run 5 | 341 | 1023.0 | transient > 10 mV: I11 48.0 mV |
| sub-008 run 1 | 347 | 1041.0 | transient > 10 mV: TI11 63.1 mV |
| sub-008 run 1 | 399 | 1197.0 | transient > 10 mV: TI11 11.7 mV |
| sub-008 run 1 | 400 | 1200.0 | transient > 10 mV: TI11 44.8 mV |
| sub-008 run 3 | 61 | 183.0 | transient > 10 mV: TI11 10.6 mV |
| sub-008 run 3 | 77 | 231.0 | transient > 10 mV: TI11 17.7 mV |
| sub-008 run 3 | 288 | 864.0 | transient > 10 mV: TI11 11.8 mV |
| sub-008 run 3 | 365 | 1095.0 | transient > 10 mV: TI11 10.7 mV |
| sub-008 run 3 | 450 | 1350.0 | transient > 10 mV: TI11 12.3 mV |
| sub-008 run 3 | 508 | 1524.0 | transient > 10 mV: TI11 12.6 mV |
| sub-008 run 4 | 405 | 1215.0 | transient > 10 mV: TI11 16.9 mV |
| sub-008 run 4 | 421 | 1263.0 | transient > 10 mV: A11 242.5 mV |
| sub-008 run 4 | 514 | 1542.0 | transient > 10 mV: TI11 74.5 mV |
| sub-008 run 5 | 192 | 576.0 | transient > 10 mV: TI11 15.6 mV |
| sub-008 run 5 | 372 | 1116.0 | transient > 10 mV: TI11 40.6 mV |
| sub-008 run 5 | 487 | 1461.0 | transient > 10 mV: TI11 32.0 mV |
| sub-008 run 5 | 489 | 1467.0 | transient > 10 mV: TI11 26.0 mV |
| sub-008 run 6 | 29 | 87.0 | transient > 10 mV: TI11 16.8 mV |
| sub-008 run 6 | 35 | 105.0 | transient > 10 mV: TI11 14.7 mV |
| sub-008 run 6 | 79 | 237.0 | transient > 10 mV: TI11 11.5 mV |
| sub-009 run 4 | 342 | 1026.0 | transient > 10 mV: F4 29.9 mV, F3 29.9 mV |

| run | HF epochs / BIDS epochs | same channel names | max abs diff HF - BIDS (V) | same bad epochs and status_description |
|---|---|---|---:|---|
| sub-001 run 2 | 483 / 483 | True | 2.5e-09 | True |
| sub-001 run 3 | 510 / 510 | True | 4.7e-10 | True |
| sub-001 run 4 | 565 / 565 | True | 9.3e-10 | True |
| sub-001 run 5 | 589 / 589 | True | 4.7e-10 | True |
| sub-001 run 6 | 499 / 499 | True | 9.3e-10 | True |
| sub-003 run 3 | 590 / 590 | True | 1.5e-08 | True |
| sub-003 run 6 | 581 / 581 | True | 4.6e-10 | True |
| sub-005 run 3 | 610 / 610 | True | 4.1e-10 | True |
| sub-005 run 4 | 610 / 610 | True | 6.5e-10 | True |
| sub-005 run 5 | 609 / 609 | True | 1.6e-09 | True |
| sub-008 run 1 | 609 / 609 | True | 3.5e-09 | True |
| sub-008 run 3 | 609 / 609 | True | 9.3e-10 | True |
| sub-008 run 4 | 593 / 593 | True | 6.0e-09 | True |
| sub-008 run 5 | 609 / 609 | True | 1.8e-09 | True |
| sub-008 run 6 | 602 / 602 | True | 5.2e-10 | True |
| sub-009 run 4 | 553 / 553 | True | 9.0e-10 | True |

The second table is the README list; the 55 rows of the third equal the `onset`, `status` and `status_description` of the
bad rows in the PR's 16 `events.tsv` (all other rows `good`, `n/a`). The last table backs the PR description: same epochs,
channels and peaks in the Hugging Face pickles, differences only float32 rounding (at most 1.5e-8 V).

**Coverage**: 67 of 67 runs (38727 of 38727 epochs); upstream comparison 16 of 16 runs with a flagged epoch.

Reproduce: `python code/receipts/2026-10-22_epochs-above-10mV.py <nm000365 root> --hf-root <Du-IN root at revision 2c85b67>`
(the NEMAR copy `sourcedata/huggingface-liulab-repository-Du-IN` also works); Python 3.15.0, numpy 2.5.4, pandas 3.1.0;
MNE not used.
