all:
	@mkdir -p data
	@mkdir -p rendu
	@rm -rf data/rendu
	@ln -sf ../rendu data/rendu
	@python3 examshell.py
