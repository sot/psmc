for week in dec2908b nov0308b sep2809b dec2809a
       do 
    ./compare_mat_py.py \
	--py_dir compdata/py_${week}/ \
	--mat_dir compdata/mat_b_${week}/ \
	--title "${week} Backstop Compare" \
	--outdir comparisons/${week}_backstop_compare ;
    done

#    ./compare_mat_py.py \
#	--py_dir compdata/py_${week}/ \
#	--mat_dir compdata/mat_d_${week}/ \
#	--title "${week} DOT Compare" \
#	--outdir comparisons/${week}_dot_compare ;
