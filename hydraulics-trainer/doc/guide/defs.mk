%.dvi: %.tex
	latex $<
	latex $<

%.pdf: %.tex
	pdflatex $<
	rm $@
	pdflatex $<

%.png.bb: %.png
	identify -format "%%%%BoundingBox: 0 0 %w %h" $< >$@

clean:
	rm -f *.aux
	rm -f *.dvi
	rm -f *.log
	rm -f *.pdf
	rm -f *.gz
	rm -f *.toc
	rm -f *.lof
	rm -f *.lot
