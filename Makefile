.PHONY: help setup frontend all clean

help:
	@echo "takeAwayBill - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make setup          Create conda environment"
	@echo ""
	@echo "Run:"
	@echo "  make frontend       Start Streamlit app (port 8501)"
	@echo "  make all            Start Streamlit app"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          Remove conda environment"
	@echo ""
	@echo "Environment:"
	@echo "  conda activate takeawaybill    Activate environment"
	@echo "  conda deactivate               Deactivate environment"

setup:
	conda env create -f environment.yaml

frontend:
	cd streamlit_app && streamlit run app.py

all:
	make frontend

clean:
	conda env remove --name takeawaybill

.PHONY: help setup frontend all clean
