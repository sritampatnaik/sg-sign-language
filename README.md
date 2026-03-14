# Sign-Lang-v2

Sign language recognition project using WLASL and MS-ASL datasets. Developed for **NUS-ISS Semester 3**.

## Overview

This repository contains code and configurations for word-level American Sign Language (ASL) recognition from video. It integrates:

- **WLASL** – Word-Level American Sign Language dataset (2,000 glosses)
- **MS-ASL** – Microsoft American Sign Language dataset (1,000 classes)
- **I3D** – Inflated 3D ConvNet for video-based recognition
- **Pose-TGCN** – Temporal Graph Convolutional Network for pose-based recognition

## Project Structure

```
Sign-Lang-v2/
├── Datasets/
│   ├── WLASL/                    # WLASL dataset & training code
│   │   ├── start_kit/             # Video download, preprocessing, data exploration
│   │   │   ├── WLASL_v0.3.json    # Full dataset metadata
│   │   │   ├── gloss_video_counts.json
│   │   │   ├── gloss_categories.json
│   │   │   └── WLASL_subset.json  # Custom subset (generated)
│   │   ├── WLASL-data.ipynb       # Data exploration & subset creation
│   │   └── code/
│   │       ├── I3D/               # I3D model training & testing
│   │       └── TGCN/              # Pose-TGCN model
│   └── MS-ASL/                    # MS-ASL dataset metadata
│       └── *.json                 # Download separately (see below)
└── README.md
```

## Setup

### Prerequisites

- Python 3.8+
- CUDA-capable GPU (recommended for training)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) (for WLASL video download)

### 1. Clone and enter the repository

```bash
git clone <your-repo-url>
cd Sign-Lang-v2
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install torch torchvision numpy
# For WLASL video download:
pip install yt-dlp
```

_(A `requirements.txt` can be added as dependencies are finalized.)_

### 4. MS-ASL dataset

The MS-ASL JSON metadata files (`MSASL_train.json`, `MSASL_test.json`, `MSASL_val.json`, etc.) are **not** included in this repo. Download them from the [MS-ASL project page](https://www.microsoft.com/en-us/research/project/ms-asl/) and place them in `Datasets/MS-ASL/`.

### 5. WLASL setup

#### Download videos

```bash
cd Datasets/WLASL/start_kit
python video_downloader.py
python preprocess.py
```

Videos will appear under `videos/`. The downloader supports resume: stop and restart to continue without re-downloading existing files.

#### Data exploration & subsets

Use `Datasets/WLASL/WLASL-data.ipynb` to explore gloss counts, classify glosses into categories (via OpenAI API), and create custom subsets by selecting glosses. See `Datasets/WLASL/README.md` for details.

#### I3D training

1. Create `Datasets/WLASL/data/` and place videos there.
2. Download [I3D weights pre-trained on Kinetics](https://drive.google.com/file/d/1JgTRHGBRCHyHRT_rAF0fOjnfiFefXkEd/view?usp=sharing) and unzip to `code/I3D/weights/`.
3. Run:
   ```bash
   cd Datasets/WLASL/code/I3D
   python train_i3d.py
   ```

#### Pose-TGCN training

1. Download [splits file](https://drive.google.com/file/d/16CWkbMLyEbdBkrxAPaxSXFP_aSxKzNN4/view?usp=sharing) and [body keypoints](https://drive.google.com/file/d/1k5mfrc2g4ZEzzNjW6CEVjLvNTZcmPanB/view?usp=sharing). Unzip into `Datasets/WLASL/data/`.
2. Adjust paths in `train_tgcn.py` main().
3. Run:
   ```bash
   cd Datasets/WLASL/code/TGCN
   python train_tgcn.py
   ```

## License

- **WLASL**: Computational Use of Data Agreement (C-UDA). Academic use only.
- **MS-ASL**: Computational Use of Data Agreement (C-UDA). See `Datasets/MS-ASL/` for details.

## References

- [WLASL](https://dxli94.github.io/WLASL/) – Word-level Deep Sign Language Recognition from Video (WACV 2020)
- [MS-ASL](https://www.microsoft.com/en-us/research/project/ms-asl/) – Microsoft American Sign Language dataset (BMVC 2019)
