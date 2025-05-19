#!/bin/bash

echo "Ініціалізація ключів у Consul..."

curl --request PUT --data "hazelcast1:5701,hazelcast2:5701,hazelcast3:5701" \
     http://localhost:8500/v1/kv/hz/cluster_members

curl --request PUT --data "msg-queue" \
     http://localhost:8500/v1/kv/hz/queue_name

echo "Конфігурація збережена у Consul!"
