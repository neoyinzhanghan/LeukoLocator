from LL.BMACounter import BMACounter

slide_name = "/media/hdd1/BMAs/H22-9756;S9;MSKC - 2023-06-13 03.24.28.ndpi"

bma_counter = BMACounter(slide_name, hoarding=True)

bma_counter.tally_differential()