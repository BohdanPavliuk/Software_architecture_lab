#!/bin/bash

for i in {1..10}; do
  curl -X POST http://localhost:8000/message \
       -H "Content-Type: application/json" \
       -d "{\"msg\": \"msg$i\"}"
  echo
  sleep 0.5
done
