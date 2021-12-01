CH_01_DEPS := \
	01_introduction.tex

guide.pdf: guide.tex $(CH_01_DEPS)
	pdflatex $<
	rm $@
	pdflatex $<

%.aux %.log %.pdf: %.tex
	pdflatex $<
	rm $@
	pdflatex $<

clean:
	rm -f *.aux
	rm -f *.log
