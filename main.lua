-- Native FireRed/LeafGreen API 2 content mod.
-- No hooks, new species, or sprite imports.
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

local function matchesVanillaExpected(current, expected)
  if type(expected) ~= "table" then return false end
  return current == expected.firered or current == expected.leafgreen
end

local grouped, mapIds, checked = {}, {}, {}
for _, p in ipairs(placements) do
  if not checked[p.species] then
    assert(
      mod.content.pokemon:get(p.species),
      "FRLG species unavailable: " .. p.species
    )
    checked[p.species] = true
  end

  assert(
    type(p.expected) == "table"
      and type(p.expected.firered) == "string"
      and type(p.expected.leafgreen) == "string",
    "missing FRLG vanilla expectations for " .. p.map
  )

  if not grouped[p.map] then
    grouped[p.map] = {}
    mapIds[#mapIds + 1] = p.map
  end
  grouped[p.map][#grouped[p.map] + 1] = p
end
table.sort(mapIds)

local lengths = { land = 12, water = 5, fishing = 10 }

for _, mapId in ipairs(mapIds) do
  local record = mod.content.encounters:get(mapId)
  local patch, valid = {}, type(record) == "table"

  for _, p in ipairs(grouped[mapId]) do
    local area = valid and record[p.terrain]
    local slots = area and area.slots
    local current = slots and slots[p.slot] and slots[p.slot].species

    if type(slots) ~= "table"
        or #slots ~= lengths[p.terrain]
        or not slots[p.slot]
        or not matchesVanillaExpected(current, p.expected) then
      valid = false
      break
    end

    if not patch[p.terrain] then
      patch[p.terrain] = { slots = copy(slots) }
    end
    patch[p.terrain].slots[p.slot].species = p.species
  end

  if valid then
    mod.content.encounters:patch(mapId, patch)
  else
    warn(
      "Skipping incompatible encounter table "
      .. mapId
      .. "; another encounter mod or engine data change may be active"
    )
  end
end
