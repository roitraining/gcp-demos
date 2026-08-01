# Creates the files for the schema autodetect Do-It-Now:
#   daily_usage_mon.csv     - Monday's big drop (100,000 rows); the vendor
#                             writes "N/A" in the minutes column for meetings
#                             that never started; Monday's N/A is at row 90,000
#   daily_usage_tue.csv     - Tuesday's small drop (1,000 rows); its N/A is
#                             at row 700
#   daily_usage_schema.json - the pinned schema used by the fixed loads
#
# Paste this whole file into a Cloud Shell terminal.

(
  echo "meeting_id,user_id,minutes,event_date"
  for i in $(seq 1 100000); do
    if [ $i -eq 90000 ]; then
      m="N/A"
    else
      m=$((RANDOM % 120 + 1))
    fi
    printf "m-%06d,u-%03d,%s,2026-07-27\n" $i $((i % 500)) $m
  done
) > daily_usage_mon.csv

(
  echo "meeting_id,user_id,minutes,event_date"
  for i in $(seq 1 1000); do
    if [ $i -eq 700 ]; then
      m="N/A"
    else
      m=$((RANDOM % 120 + 1))
    fi
    printf "m-%06d,u-%03d,%s,2026-07-28\n" $i $((i % 50)) $m
  done
) > daily_usage_tue.csv

cat > daily_usage_schema.json <<'EOF'
[
  {"name": "meeting_id", "type": "STRING"},
  {"name": "user_id", "type": "STRING"},
  {"name": "minutes", "type": "INTEGER"},
  {"name": "event_date", "type": "DATE"}
]
EOF

echo "Created daily_usage_mon.csv, daily_usage_tue.csv, and daily_usage_schema.json"
