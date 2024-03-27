import random
import os
import tqdm
from LL.BMACounter import BMACounter
from LL.resources.BMAassumptions import *


def already_processed(fname, dump_dirs):
    for dump_dir in dump_dirs:
        if dump_dir in fname:
            return True

    return False


# get a list of all directories in the dump_dir
dump_dirs = [
    dname
    for dname in os.listdir(dump_dir)
    if os.path.isdir(os.path.join(dump_dir, dname))
]

source_dir = "/media/hdd1/BMAs"

# make sure to only keep things with ndpi extension
slides = [
    [
        "H19-1881;S9;MSK0 - 2023-06-20 22.50.56.ndpi",
        "H20-7511;S10;MSK0 - 2023-12-20 13.54.32.ndpi",
        "H19-2847;S10;MSKE - 2023-08-16 13.03.26.ndpi",
        "H21-5243;S9;MSKZ - 2023-05-23 22.10.23.ndpi",
        "H16-6373;S10;MSK0 - 2023-03-24 19.27.11.ndpi",
        "H23-8651;S14;MSK3 - 2023-12-11 21.37.08.ndpi",
        "H18-9196;S10;MSKH - 2023-06-21 19.44.20.ndpi",
        "H18-1228;S10;MSK6 - 2023-09-13 16.54.34.ndpi",
        "H20-4826;S10;MSKF - 2023-08-31 08.10.48.ndpi",
        "H18-6780;S10;MSKN - 2023-06-26 17.01.54.ndpi",
        "H20-5979;S10;MSKP - 2023-06-13 00.06.32.ndpi",
        "H19-1581;S10;MSK9 - 2023-06-22 01.34.35.ndpi",
        "H23-852;S11;MSKV - 2023-06-13 06.22.51.ndpi",
        "H21-7444;S9;MSK4 - 2023-09-27 23.40.40.ndpi",
        "H18-9949;S10;MSKN - 2023-03-23 21.18.36.ndpi",
        "H22-3519;S10;MSK6 - 2023-06-05 22.55.57.ndpi",
        "H19-9313;S9;MSK8 - 2023-06-21 20.19.36.ndpi",
        "H19-3301;S10;MSKA - 2023-09-06 20.41.29.ndpi",
        "H20-7861;S2;MSK9 - 2023-05-10 13.47.02.ndpi",
        "H20-3800;S10;MSKQ - 2023-06-05 10.26.22.ndpi",
        "H19-5709;S10;MSKO - 2023-09-05 12.57.14.ndpi",
        "H22-1038;S10;MSK0 - 2023-05-26 21.14.45.ndpi",
        "H22-5220;S11;MSKY - 2023-05-26 07.39.21.ndpi",
        "H19-7702;S10;MSKJ - 2023-05-24 17.23.24.ndpi",
        "H19-8879;S9;MSKN - 2023-04-25 12.52.12.ndpi",
        "H17-2658;S3;MSK5 - 2023-08-25 00.10.47.ndpi",
        "H23-602;S9;MSK5 - 2023-06-13 09.28.01.ndpi",
        "H18-1807;S10;MSKI - 2023-08-16 09.28.08.ndpi",
        "H22-1634;S10;MSK2 - 2023-06-12 15.34.38.ndpi",
        "H19-3560;S1;MSK8 - 2023-08-16 13.20.52.ndpi",
        "H20-5680;S10;MSKO - 2023-06-07 04.47.24.ndpi",
        "H18-2615;S6;MSK2 - 2023-05-31 14.46.04.ndpi",
        "H22-10964;S15;MSKC - 2023-08-31 21.17.02.ndpi",
        "H19-582;S10;MSK9 - 2023-09-12 00.43.02.ndpi",
        "H20-6374;S10;MSKF - 2023-08-10 12.03.40.ndpi",
        "H18-9859;S10;MSKN - 2023-09-21 17.29.19.ndpi",
        "H22-9421;S15;MSKZ - 2023-09-27 16.07.00.ndpi",
        "H19-9819;S10;MSKK - 2023-08-16 17.50.48.ndpi",
        "H20-4048;S10;MSKL - 2023-08-16 21.06.42.ndpi",
        "H18-5240;S6;MSK9 - 2023-10-23 11.47.25.ndpi",
        "H18-2964;S10;MSKD - 2023-05-31 14.28.51.ndpi",
        "H18-4382;S1;MSK- - 2023-06-28 15.26.26.ndpi",
        "H18-8004;S10;MSKO - 2023-06-26 10.33.10.ndpi",
        "H22-2521;S9;MSKW - 2023-05-26 19.21.40.ndpi",
        "H19-8365;S9;MSKD - 2023-10-09 10.45.59.ndpi",
        "H20-5669;S10;MSKL - 2023-09-13 12.42.03.ndpi",
        "H22-1844;S9;MSK3 - 2023-05-26 13.22.39.ndpi",
        "H21-959;S10;MSK0 - 2023-09-27 18.00.32.ndpi",
        "H21-2246;S10;MSK1 - 2023-05-17 18.13.44.ndpi",
        "H18-669;S6;MSK9 - 2023-09-21 15.30.31.ndpi",
        "H18-2870;S10;MSKJ - 2023-08-16 08.28.40.ndpi",
        "H19-9472;S10;MSKF - 2023-09-05 17.54.31.ndpi",
        "H19-4004;S9;MSKJ - 2023-05-25 02.02.07.ndpi",
        "H19-380;S10;MSKE - 2023-09-01 00.25.25.ndpi",
        "H18-7593;S10;MSKG - 2023-08-24 15.00.40.ndpi",
        "H22-302;S1;MSKT - 2023-05-10 15.44.28.ndpi",
        "H18-269;S10;MSK0 - 2023-09-21 18.51.43.ndpi",
        "H19-5752;S11;MSK4 - 2023-05-24 22.54.50.ndpi",
        "H21-8956;S9;MSKC - 2023-05-19 12.00.34.ndpi",
        "H20-1752;S10;MSKA - 2023-09-13 18.09.46.ndpi",
        "H18-6519;S14;MSK8 - 2023-09-21 15.59.00.ndpi",
        "H21-4310;S10;MSK5 - 2023-09-27 20.20.14.ndpi",
        "H18-2272;S10;MSK6 - 2023-08-31 11.56.14.ndpi",
        "H18-7259;S10;MSKF - 2023-09-18 19.02.57.ndpi",
        "H17-3537;S10;MSK0 - 2023-04-27 15.58.37.ndpi",
        "H21-9716;S2;MSK1 - 2023-10-17 11.06.59.ndpi",
        "H22-6733;S15;MSK2 - 2024-01-02 19.07.13.ndpi",
        "H22-9891;S14;MSK9 - 2023-06-12 18.24.19.ndpi",
        "H22-7742;S9;MSK6 - 2023-06-06 14.10.45.ndpi",
        "H20-6024;S1;MSK8 - 2023-09-21 12.59.26.ndpi",
        "H21-182;S9;MSKW - 2023-05-17 07.43.11.ndpi",
        "H18-4760;S10;MSKJ - 2023-06-28 19.45.30.ndpi",
        "H19-8400;S10;MSKP - 2023-04-25 13.25.36.ndpi",
        "H21-3591;S10;MSK5 - 2024-01-02 22.21.05.ndpi",
        "H16-3568;S6;MSK8 - 2023-03-24 17.25.38.ndpi",
        "H19-1901;S9;MSKC - 2023-09-11 22.44.37.ndpi",
        "H20-7312;S10;MSK9 - 2023-07-05 14.37.56.ndpi",
        "H21-4994;S1;MSK3 - 2023-05-23 23.49.24.ndpi",
        "H19-9604;S10;MSKM - 2023-12-11 19.42.40.ndpi",
        "H19-6022;S10;MSKD - 2023-09-06 19.50.25.ndpi",
        "H22-550;S11;MSKZ - 2023-06-01 04.00.21.ndpi",
        "H23-1211;S14;MSKO - 2023-09-11 15.02.39.ndpi",
        "H18-7324;S6;MSK4 - 2023-08-24 15.11.54.ndpi",
        "H18-4098;S6;MSKI - 2023-09-21 20.44.29.ndpi",
        "H18-4371;S6;MSK3 - 2023-09-21 15.36.44.ndpi",
        "H19-8205;S10;MSKI - 2023-05-24 15.50.58.ndpi",
        "H18-945;S10;MSKA - 2023-06-05 16.29.37.ndpi",
        "H19-9111;S10;MSK6 - 2023-06-26 17.37.00.ndpi",
        "H22-5211;S14;MSKR - 2023-09-06 12.47.56.ndpi",
        "H21-4922;S10;MSK4 - 2024-01-03 18.39.33.ndpi",
        "H21-8887;S10;MSKH - 2023-05-19 12.40.48.ndpi",
        "H22-4142;S1;MSKP - 2023-09-12 15.21.47.ndpi",
        "H19-1470;S10;MSKF - 2023-09-11 16.13.20.ndpi",
        "H20-3960;S10;MSKN - 2023-08-24 12.47.57.ndpi",
        "H16-5481;S9;MSK7 - 2023-09-28 05.31.24.ndpi",
        "H22-10170;S9;MSKE - 2023-10-02 13.29.40.ndpi",
        "H21-6221;S10;MSKY - 2023-05-23 19.45.11.ndpi",
        "H23-4668;S10;MSKC - 2023-12-12 07.40.52.ndpi",
        "H20-4241;S10;MSK7 - 2023-06-05 14.41.51.ndpi",
        "H21-3486;S10;MSK8 - 2023-05-17 10.16.21.ndpi",
    ]
]

print(slides)

# randomly shuffle the slides and select 100
random.shuffle(slides)

for bma_fname in tqdm(slides, desc="Processing BMA slides"):

    if already_processed(bma_fname, dump_dirs):
        print("Already processed", bma_fname)
        continue

    print("Processing", bma_fname)

    # try:
    bma_slide_path = os.path.join(source_dir, bma_fname)
    bma_counter = BMACounter(
        bma_slide_path,
        hoarding=True,
        continue_on_error=True,
        do_extract_features=False,
    )
    bma_counter.tally_differential()

    print("Saving to", bma_counter.save_dir)
