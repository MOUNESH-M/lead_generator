"""
main.py — Entry point. Runs the full pipeline via run_pipeline.py
Just run: python run_pipeline.py
"""
import runpy
runpy.run_path("run_pipeline.py", run_name="__main__")
