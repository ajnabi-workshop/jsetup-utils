#!/usr/bin/env bash

if [ ! -f .env ]; then
  cp jsetup-utils/.env-template .env
fi