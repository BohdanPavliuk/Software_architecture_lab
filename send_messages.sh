#!/bin/bash

for i in {1..10}; do
  curl -X POST http://localhost:8001/log \
       -H "Content-Type: application/json" \
       -d "{\"key\": \"msg$i\", \"value\": \"Hello $i\"}"
  echo  
  sleep 0.5
done
