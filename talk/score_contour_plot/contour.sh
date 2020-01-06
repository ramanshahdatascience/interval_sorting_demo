#! /bin/bash

gnuplot << EOF && open plot.png
set term png
set output 'plot.png'
set view map
set size square
unset surface
set contour
set cntrparam levels 10
set clabel "%.1f"
set isosamples 150
splot [0:1] [0:1] y + 0.5 * x ** 2 - 0.5 * y ** 2
EOF
