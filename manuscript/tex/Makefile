# Build the report. arXiv: upload *.tex, references.bib and main.bbl from this directory (flat).
main.pdf: $(wildcard *.tex) references.bib
	-pdflatex -interaction=nonstopmode main >/dev/null
	-bibtex main >/dev/null
	-pdflatex -interaction=nonstopmode main >/dev/null
	-pdflatex -interaction=nonstopmode main >/dev/null
clean:
	rm -f main.aux main.log main.out main.blg main.toc
