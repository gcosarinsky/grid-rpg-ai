MAP_GEN_PROMPT = """
You generate structured maps for a grid-based exploration RPG.

Return only valid JSON.
Do not include explanations.
Do not include markdown.

Constraints:
- Grid size: {width}x{height}
- Theme: {theme}
- Tone: dark, concise, exploration-focused
- Biomes allowed: {allowed_biomes}
- Maximum named locations: {max_pois}
- Required locations: start, goal
- Optional locations: town, ruins, shrine, road, forest, cave
- The map must be traversable.
- There must be at least one valid path from start to goal.
- Keep the layout simple enough for an MVP.

Output schema:
{
  "width": int,
  "height": int,
  "tiles": [[biome_key, ...]],
  "regions": [
    {"id": str, "type": str, "bounds": [[x,y], [x,y]]}
  ],
  "pois": [
    {
      "id": str,
      "kind": str,
      "name": str,
      "position": [x, y],
      "tags": [str]
    }
  ],
  "start": [x, y],
  "goal": [x, y],
  "hooks": [
    {"type": str, "text": str, "poi_id": str}
  ]
}

Rules:
- Use short biome keys.
- Keep POIs sparse and meaningful.
- Do not place POIs outside the grid.
- Do not block every route with hazards.
- Make the world feel coherent geographically.
"""