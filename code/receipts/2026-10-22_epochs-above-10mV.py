import argparse
import pickle
import re
from pathlib import Path

import numpy as np
import pandas as pd
from numpy._core import multiarray

THRESHOLD = 0.01  # V
HF_RUN = "data/seeg.he2023xuanwu/{sub}/word-recitation/run{run}/dataset.bipolar.default.unaligned"


class DotDict(dict):
    pass


ALLOWED = {
    ("utils.DotDict", "DotDict"): DotDict,
    ("numpy", "ndarray"): np.ndarray,
    ("numpy", "dtype"): np.dtype,
    ("numpy.core.multiarray", "_reconstruct"): multiarray._reconstruct,
    ("numpy._core.multiarray", "_reconstruct"): multiarray._reconstruct,
    ("numpy.core.multiarray", "scalar"): multiarray.scalar,
    ("numpy._core.multiarray", "scalar"): multiarray.scalar,
}


class RestrictedUnpickler(pickle.Unpickler):
    def find_class(self, module: str, name: str):
        if (module, name) not in ALLOWED:
            raise pickle.UnpicklingError(f"{module}.{name} not allowed")
        return ALLOWED[(module, name)]


def load_pickle(path: Path):
    with open(path, "rb") as f:
        return RestrictedUnpickler(f).load()


def read_brainvision(vhdr: Path) -> tuple[list[str], np.ndarray, float]:
    header = vhdr.read_text(encoding="utf-8")
    assert "BinaryFormat=IEEE_FLOAT_32" in header and "DataOrientation=MULTIPLEXED" in header, vhdr
    channels = re.findall(r"^Ch\d+=([^,]*),[^,]*,([^,]*),(.*)$", header, re.M)
    assert all(float(res) == 1 and unit == "V" for _, res, unit in channels), f"{vhdr}: not 1 V/unit: {channels}"
    sfreq = 1e6 / float(re.search(r"^SamplingInterval=([\d.]+)", header, re.M).group(1))
    data = np.fromfile(vhdr.with_suffix(".eeg"), dtype="<f4").reshape(-1, len(channels))
    return [name for name, _, _ in channels], data, sfreq


def describe(names: list[str], peaks: np.ndarray) -> str:
    hits = sorted((-peaks[j], j) for j in np.flatnonzero(peaks > THRESHOLD))
    return "transient > 10 mV: " + ", ".join(f"{names[j]} {-p * 1e3:.1f} mV" for p, j in hits)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, help="nm000365 dataset root")
    parser.add_argument("--hf-root", type=Path, help=f"Hugging Face liulab-repository/Du-IN root ({HF_RUN}/data, info)")
    args = parser.parse_args()

    epoch_max, flagged, hf_rows = [], [], []
    vhdrs = sorted(args.root.glob("sub-*/ieeg/*_ieeg.vhdr"))
    for vhdr in vhdrs:
        names, data, sfreq = read_brainvision(vhdr)
        events = pd.read_csv(vhdr.with_name(vhdr.name.replace("_ieeg.vhdr", "_events.tsv")), sep="\t")
        n = int(round(events["duration"].iloc[0] * sfreq))
        assert (events["duration"] * sfreq == n).all() and (events["sample"] == np.arange(len(events)) * n).all(), vhdr
        assert len(events) * n == len(data), vhdr
        epochs = data.reshape(len(events), n, len(names))
        peaks = np.abs(epochs).max(axis=1).astype(np.float64)  # (n_epochs, n_channels)
        epoch_max.extend(peaks.max(axis=1))
        sub, run = re.match(r"sub-(\d+)_task-wordreading_run-(\d+)", vhdr.name).groups()
        bad = np.flatnonzero(peaks.max(axis=1) > THRESHOLD)
        for k in bad:
            flagged.append({"run": f"sub-{sub} run {run}", "source_epoch_index": int(events["source_epoch_index"][k]),
                            "onset": events["onset"][k], "status_description": describe(names, peaks[k])})
        if args.hf_root is None or len(bad) == 0:
            continue
        hf = args.hf_root / HF_RUN.format(sub=sub, run=run)
        items = load_pickle(hf / "data")
        source = np.stack([items[i]["data_s"] for i in events["source_epoch_index"]]).transpose(0, 2, 1)
        source_peaks = np.abs(source).max(axis=1)
        same_flags = np.array_equal(np.flatnonzero(source_peaks.max(axis=1) > THRESHOLD), bad)
        hf_rows.append((
            f"sub-{sub} run {run}",
            f"{len(items)} / {len(events)}",
            list(load_pickle(hf / "info")["ch_names"]) == names,
            f"{np.abs(source - epochs).max():.1e}",
            same_flags and all(describe(names, source_peaks[k]) == describe(names, peaks[k]) for k in bad),
        ))

    flagged = pd.DataFrame(flagged)
    print("| quantity | value |\n|---|---|")
    print(f"| runs | {len(vhdrs)} |")
    print(f"| epochs | {len(epoch_max)} |")
    print(f"| median epoch max abs value (all channels) | {np.median(epoch_max) * 1e3:.2f} mV |")
    print(f"| epochs with max abs value > 10 mV (status bad) | {len(flagged)} in {flagged['run'].nunique()} runs |")

    print("\n| run | bad source_epoch_index |\n|---|---|")
    for run, group in flagged.groupby("run", sort=False):
        print(f"| {run} | {', '.join(map(str, group['source_epoch_index']))} |")

    print("\n| run | source_epoch_index | onset (s) | status_description |\n|---|---:|---:|---|")
    for r in flagged.itertuples():
        print(f"| {r.run} | {r.source_epoch_index} | {r.onset} | {r.status_description} |")

    if hf_rows:
        print("\n| run | HF epochs / BIDS epochs | same channel names | max abs diff HF - BIDS (V) "
              "| same bad epochs and status_description |\n|---|---|---|---:|---|")
        for row in hf_rows:
            print("| " + " | ".join(map(str, row)) + " |")


if __name__ == "__main__":
    main()
