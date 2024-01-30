from LL.BMACounter import BMACounter

slide_name = "/media/hdd1/BMAs/H23-9637;S10;MSKD - 2023-12-11 23.36.32.ndpi"

bma_counter = BMACounter(slide_name, hoarding=True)

bma_counter.tally_differential()