#
# makefile
#  
# Made by Carlos Linares
# Login   <clinareskorf.plg.inf.uc3m.es>
# -----------------------------------------------------------------------------

# Macro Definitions 
# ------------------------------------------
LATEX 	= latex
DVIPS   = dvips
PSPDF   = ps2pdf
RM 	= /bin/rm -f 	

.SUFFIXES: .tex .dvi .ps .pdf

.tex.dvi:
	$(LATEX) $<

.dvi.ps:
	$(DVIPS) -Ppdf -G0 $<

.ps.pdf:
	$(PSPDF) $<


/* Local Variables: */
/* mode:makefile */
/* fill-column:80 */
/* End: */
