#!/bin/bash
cd /Users/hiroakinishida/Desktop/Dev/scraper
source .venv/bin/activate
uvicorn main:app --reload
