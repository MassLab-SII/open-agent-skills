# Itinerary Filter Skill - Quick Start

## File Location
```
skills/japan_travel_planner/remove_osaka_itinerary.py
```

## Basic Command
```bash
python3 skills/japan_travel_planner/remove_osaka_itinerary.py remove
```

## Common Use Cases

### Remove Osaka items after 6 PM (Day 1 & 2)
```bash
python3 skills/japan_travel_planner/remove_osaka_itinerary.py remove
```

### Remove specific location after specific time
```bash
python3 skills/japan_travel_planner/remove_osaka_itinerary.py remove \
  --location "LOCATION_NAME" \
  --cutoff-time HOUR
```

### Full example: Remove Tokyo items after 7 PM (Day 1 & 2)
```bash
python3 skills/japan_travel_planner/remove_osaka_itinerary.py remove \
  --location "Tokyo" \
  --cutoff-time 19
```

### Full example: Remove Kyoto items after 8 PM (Day 3 & 4)
```bash
python3 skills/japan_travel_planner/remove_osaka_itinerary.py remove \
  --location "Kyoto" \
  --days "Day 3" "Day 4" \
  --cutoff-time 20
```

## Parameter Mapping

| Parameter | Format | Example |
|-----------|--------|---------|
| `--location` | Exact string from database | `"Osaka"` `"Tokyo"` `"Kyoto"` |
| `--days` | List of day names | `"Day 1" "Day 2"` or `"Day 1" "Day 2" "Day 3"` |
| `--cutoff-time` | 24-hour format (0-23) | 18=6PM, 19=7PM, 20=8PM, 21=9PM |

## Key Notes

1. **Time Logic**: Removes items AFTER cutoff time (not including exact time)
   - `--cutoff-time 18` removes items after 6 PM but KEEPS items AT 6 PM
   
2. **Location Match**: Must match exactly with "Group" property in database
   - Use "OSAKA", "Tokyo", "Kyoto", etc. as they appear in the database

3. **Days Format**: Always use "Day 1", "Day 2" format or match database exactly

4. **Default Behavior**: With no parameters, removes Osaka items after 6 PM from Day 1 & 2

## Help
```bash
python3 skills/japan_travel_planner/remove_osaka_itinerary.py --help
```
