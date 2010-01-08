#!/usr/bin/env python
import sys
import numpy as np
from Ska.TelemArchive.fetch import fetch
from Chandra.Time import DateTime
from Ska.DBI import DBI

def db_state0( starttime ):
    stime = DateTime(starttime)
    db = DBI(dbi='sybase', server='sybase', user='aca_read', database='aca')
    query = """select * from cmd_states
               where datestart =
               (select max(datestart) from cmd_states
                where datestart < '%s')""" % stime.date
    state0 = db.fetchone( query )
    return state0

def fetch_temps( starttime ):
    (telem_hdr,telem_val) = fetch(start=DateTime(starttime).secs, 
                                  stop=( DateTime(starttime).secs+1),colspecs=['1pdeaat,1pin1at'])
    telem = np.rec.fromrecords( telem_val, names=telem_hdr)
    return telem

def print_state_from_time( stime ):
    state0 = db_state0( stime )
    temps = fetch_temps( stime )
    matlab_state = {'temptime' : DateTime(stime).date }
    for field in ('datestart', 'datestop', 'simpos', 'fep_count', 'ccd_count', 'clocking', 'vid_board'):
        print field, state0[field]
    for field in ('1pdeaat', '1pin1at'):
        print field, temps[0][field]


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        print_state_from_time(arg)
        


            
