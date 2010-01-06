import Ska.Table
## /proj/sot/ska/bin/fetch \
##   --start 2008-01-01T00:00:00 \
##   --stop 2008-02-01T00:00:00 \
##   --dt 32.8 --time-format secs \
##    tscpos \
##    point_suncentang \
##    1pdeaat 1pin1at \
##    1de28avo 1deicacu \
##    1dp28avo 1dpicacu \
##    1dp28bvo 1dpicbcu \
##    >! telem_01.dat

ascii = 'telem_01.dat'
fits = 'telem_01.fits'

tbl = Ska.Table.read_ascii_table(ascii)
Ska.Table.write_fits_table(fits, tbl)

