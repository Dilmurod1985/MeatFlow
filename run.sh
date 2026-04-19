#!/usr/bin/env bash
export PYTHONPATH=./app
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
