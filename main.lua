-- Native FireRed API 2 content mod. No hooks, new species, or sprite imports.
local mod = ...
local source = assert(mod:read("data/placements.lua"), "missing data/placements.lua")
local placements = assert(load(source, "@firered_johto_hoenn/placements", "t", {}))()

local function copy(value)
  if type(value) ~= "table" then return value end
  local out = {}
  for k, v in pairs(value) do out[k] = copy(v) end
  return out
end

local function warn(message)
  if mod.log and mod.log.warn then mod.log:warn(message) end
end

-- Preflight before registering anything. A Hoenn National Dex number is NOT
-- its internal GBA species ID; the registry resolves these symbolic names.
local grouped, mapIds, checked = {}, {}, {}
for _, p in ipairs(placements) do
  if not checked[p.species] then
    assert(mod.content.pokemon:get(p.species), "FireRed species unavailable: " .. p.species)
    checked[p.species] = true
  end
  if not grouped[p.map] then
    grouped[p.map] = {}
    mapIds[#mapIds + 1] = p.map
  end
  grouped[p.map][#grouped[p.map] + 1] = p
end
table.sort(mapIds)

local groups = {
  land = { {1,12} }, water = { {1,5} },
  fishing = { {1,2}, {3,5}, {6,10} },
}
local lengths = { land = 12, water = 5, fishing = 10 }
local function preservesNative(before, after, terrain)
  for _, bounds in ipairs(groups[terrain]) do
    local kept = {}
    for i = bounds[1], bounds[2] do kept[after[i].species] = true end
    for i = bounds[1], bounds[2] do
      if not kept[before[i].species] then return false end
    end
  end
  return true
end

for _, mapId in ipairs(mapIds) do
  local record = mod.content.encounters:get(mapId)
  local patch, valid = {}, type(record) == "table"
  for _, p in ipairs(grouped[mapId]) do
    local area = valid and record[p.terrain]
    local slots = area and area.slots
    if type(slots) ~= "table" or #slots ~= lengths[p.terrain]
        or not slots[p.slot] or slots[p.slot].species ~= p.expected then
      valid = false
      break
    end
    if not patch[p.terrain] then patch[p.terrain] = { slots = copy(slots) } end
    patch[p.terrain].slots[p.slot].species = p.species
  end
  if valid then
    for terrain, area in pairs(patch) do
      if not preservesNative(record[terrain].slots, area.slots, terrain) then
        valid = false
        break
      end
    end
  end
  if valid then
    -- Full-length lists replace; appending slots would not change FireRed's
    -- fixed 12/5/10-slot rolls. Leave rates and all live level ranges intact.
    mod.content.encounters:patch(mapId, patch)
  else
    warn("Skipping incompatible encounter table " .. mapId .. "; another encounter mod or engine data change may be active")
  end
end
